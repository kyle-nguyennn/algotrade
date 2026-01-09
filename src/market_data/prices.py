from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple, Union

import pandas as pd

# Note: pandas_datareader's Yahoo backend is sometimes blocked by Yahoo (HTTP 404/consent pages).
# We still try it first (as requested), but fall back to `yfinance` when needed.
from pandas_datareader import data as pdr


def _default_data_dir() -> Path:
    # When running via `python src/main.py`, cwd is usually the repo root.
    # This keeps a robust default that works even if cwd changes.
    return Path(__file__).resolve().parents[2] / "data"


def _to_date(value: Union[str, date, datetime, pd.Timestamp]) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str):
        return pd.Timestamp(value).date()
    raise TypeError(f"Unsupported date type: {type(value)}")


def _batched_date_ranges(start: date, end: date, batch_days: int) -> Iterator[Tuple[date, date]]:
    if batch_days <= 0:
        raise ValueError("batch_days must be > 0")
    cur = start
    while cur <= end:
        batch_end = min(end, cur + timedelta(days=batch_days - 1))
        yield cur, batch_end
        cur = batch_end + timedelta(days=1)


def iter_close_from_csv(prices_csv_path: str) -> Iterator[Tuple[str, float]]:
    """Iterator over (date_str, close) from a CSV with at least columns: date, close."""
    with open(prices_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row["date"], float(row["close"])


@dataclass(frozen=True)
class YahooPriceStore:
    """Fetches daily OHLCV data from Yahoo via pandas_datareader with parquet caching.

    Cache layout (partitioned by date):
            data/prices/yahoo/{symbol}/YYYY-MM-DD/part-*.parquet
      data/prices/yahoo/{symbol}/_meta.json

    The iterator methods stream data in batches to avoid large in-memory frames.
    """

    data_dir: Path

    @staticmethod
    def default() -> "YahooPriceStore":
        return YahooPriceStore(data_dir=_default_data_dir())

    def _symbol_root(self, symbol: str) -> Path:
        return self.data_dir / "prices" / "yahoo" / symbol.upper()

    def _meta_path(self, symbol: str) -> Path:
        return self._symbol_root(symbol) / "_meta.json"

    def _read_meta(self, symbol: str) -> Optional[dict]:
        p = self._meta_path(symbol)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write_meta(self, symbol: str, meta: dict) -> None:
        root = self._symbol_root(symbol)
        root.mkdir(parents=True, exist_ok=True)
        self._meta_path(symbol).write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

    def _cache_covers(self, symbol: str, start: date, end: date) -> bool:
        meta = self._read_meta(symbol)
        if not meta:
            return False
        try:
            min_d = _to_date(meta["min_date"])
            max_d = _to_date(meta["max_date"])
        except Exception:
            return False
        return min_d <= start and max_d >= end

    def _update_meta_range(self, symbol: str, batch_min: date, batch_max: date) -> None:
        meta = self._read_meta(symbol) or {}
        if "min_date" in meta:
            cur_min = _to_date(meta["min_date"])
            cur_max = _to_date(meta["max_date"])
            new_min = min(cur_min, batch_min)
            new_max = max(cur_max, batch_max)
        else:
            new_min, new_max = batch_min, batch_max
        self._write_meta(symbol, {"min_date": new_min.isoformat(), "max_date": new_max.isoformat()})

    def _ensure_pyarrow(self):
        try:
            import pyarrow  # type: ignore[import-not-found]  # noqa: F401
            import pyarrow.dataset  # type: ignore[import-not-found]  # noqa: F401
        except Exception as e:
            raise RuntimeError(
                "Parquet caching requires `pyarrow`. Install with: pip install pyarrow"
            ) from e

    def _write_partitioned_parquet(self, symbol: str, frame: pd.DataFrame) -> None:
        """Write a pandas DataFrame with a `date` column partitioned by date (directory style)."""
        self._ensure_pyarrow()
        import pyarrow as pa  # type: ignore[import-not-found]
        import pyarrow.dataset as ds  # type: ignore[import-not-found]

        root = self._symbol_root(symbol)
        root.mkdir(parents=True, exist_ok=True)

        df = frame.copy()
        if "date" not in df.columns:
            raise ValueError("DataFrame must contain 'date' column")
        df["date"] = pd.to_datetime(df["date"]).dt.date

        table = pa.Table.from_pandas(df, preserve_index=False)

        partitioning = ds.partitioning(
            pa.schema([("date", pa.date32())]),
            # DirectoryPartitioning (default): YYYY-MM-DD/ (no key name prefix)
        )

        # PyArrow API differs by version; try to preserve existing cached partitions.
        try:
            ds.write_dataset(
                data=table,
                base_dir=str(root),
                format="parquet",
                partitioning=partitioning,
                existing_data_behavior="overwrite_or_ignore",
            )
        except TypeError:
            # Fallback: write to temp and merge partitions.
            import shutil
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                ds.write_dataset(
                    data=table,
                    base_dir=tmp,
                    format="parquet",
                    partitioning=partitioning,
                )
                for child in Path(tmp).iterdir():
                    dest = root / child.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(child, dest)

    def _fetch_yahoo(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """Fetch from Yahoo (daily).

        Primary path uses `pandas_datareader` (requested). If Yahoo blocks it (common), we fall back to
        `yfinance` when available.
        """

        def _fetch_with_yfinance() -> pd.DataFrame:
            try:
                import yfinance as yf  # type: ignore[import-not-found]
            except Exception as e:
                raise RuntimeError(
                    "Yahoo fetch via pandas_datareader failed (likely blocked by Yahoo). "
                    "Install a fallback provider with: pip install yfinance"
                ) from e

            # yfinance expects strings/datetimes; end is exclusive-ish depending on provider.
            ydf = yf.download(
                symbol,
                start=pd.Timestamp(start),
                end=pd.Timestamp(end) + pd.Timedelta(days=1),
                progress=False,
                auto_adjust=False,
                actions=False,
                threads=True,
            )
            if ydf is None or ydf.empty:
                return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])

            # yfinance may return MultiIndex columns (e.g., ('Open','SPY') or ('SPY','Open')).
            if isinstance(ydf.columns, pd.MultiIndex):
                expected = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
                levels = [set(map(str, ydf.columns.get_level_values(i))) for i in range(ydf.columns.nlevels)]
                if expected.issubset(levels[0]):
                    ydf.columns = ydf.columns.get_level_values(0)
                elif len(levels) > 1 and expected.issubset(levels[1]):
                    ydf.columns = ydf.columns.get_level_values(1)
                else:
                    ydf.columns = ["_".join(map(str, t)).strip() for t in ydf.columns]

            ydf = ydf.reset_index().rename(
                columns={
                    "Date": "date",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            )

            # Normalize columns
            ydf.columns = [str(c).strip().lower().replace(" ", "_") for c in ydf.columns]
            keep = [c for c in ["date", "open", "high", "low", "close", "adj_close", "volume"] if c in ydf.columns]
            return ydf[keep].sort_values("date")

        # pandas_datareader expects datetime-like
        try:
            df = pdr.get_data_yahoo(
                symbol,
                start=pd.Timestamp(start),
                end=pd.Timestamp(end) + pd.Timedelta(days=1),
            )
        except Exception as e:
            # Yahoo frequently returns 404/consent pages to programmatic clients.
            try:
                from pandas_datareader._utils import RemoteDataError
            except Exception:
                RemoteDataError = Exception  # type: ignore[assignment]

            if isinstance(e, RemoteDataError) or "Unable to read URL" in str(e):
                df = _fetch_with_yfinance()
            else:
                raise
        if df is None or df.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])

        df = df.reset_index().rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )

        # Normalize columns in case provider changes casing
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Keep only expected columns if present
        keep = [c for c in ["date", "open", "high", "low", "close", "adj_close", "volume"] if c in df.columns]
        return df[keep].sort_values("date")

    def load_range(self, symbol: str, start: Union[str, date, datetime, pd.Timestamp], end: Union[str, date, datetime, pd.Timestamp], *, batch_days: int = 365) -> pd.DataFrame:
        """Return a DataFrame of cached prices for [start,end], fetching and caching if needed."""
        s = _to_date(start)
        e = _to_date(end)
        if not self._cache_covers(symbol, s, e):
            for bs, be in _batched_date_ranges(s, e, batch_days=batch_days):
                if self._cache_covers(symbol, bs, be):
                    continue
                fetched = self._fetch_yahoo(symbol, bs, be)
                if not fetched.empty:
                    self._write_partitioned_parquet(symbol, fetched)
                    self._update_meta_range(symbol, bs, be)

        self._ensure_pyarrow()
        import pyarrow as pa  # type: ignore[import-not-found]
        import pyarrow.dataset as ds  # type: ignore[import-not-found]

        root = self._symbol_root(symbol)
        if not root.exists():
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "adj_close", "volume"])

        # Prefer directory-style partitions (YYYY-MM-DD/). If the cache was created previously with hive
        # style (date=YYYY-MM-DD/), fall back to hive for backward compatibility.
        has_hive_dirs = any(p.is_dir() and p.name.startswith("date=") for p in root.iterdir())
        if not has_hive_dirs:
            partitioning = ds.partitioning(
                pa.schema([("date", pa.date32())]),
            )
            dataset = ds.dataset(str(root), format="parquet", partitioning=partitioning)
        else:
            dataset = ds.dataset(str(root), format="parquet", partitioning="hive")

        start_d = pd.Timestamp(s).date()
        end_d = pd.Timestamp(e).date()

        # For directory-style partitions with an explicit schema, comparisons should work with date32.
        # For some hive-style datasets, the partition value may be inferred as string.
        try:
            filt = (ds.field("date") >= start_d) & (ds.field("date") <= end_d)
            table = dataset.to_table(filter=filt)
        except Exception:
            filt = (ds.field("date") >= start_d.isoformat()) & (ds.field("date") <= end_d.isoformat())
            table = dataset.to_table(filter=filt)
        out = table.to_pandas()
        if "date" in out.columns:
            out["date"] = pd.to_datetime(out["date"]).dt.date
        return out.sort_values("date")

    def iter_close_prices(
        self,
        symbol: str,
        start: Union[str, date, datetime, pd.Timestamp],
        end: Union[str, date, datetime, pd.Timestamp],
        *,
        batch_days: int = 365,
        prefer_adj_close: bool = False,
    ) -> Iterator[Tuple[str, float]]:
        """Stream (date_str, close) for the requested range.

        Uses batched fetch + cache and yields rows in ascending date order.
        """
        s = _to_date(start)
        e = _to_date(end)

        for bs, be in _batched_date_ranges(s, e, batch_days=batch_days):
            df = self.load_range(symbol, bs, be, batch_days=batch_days)
            if df.empty:
                continue
            price_col = "adj_close" if (prefer_adj_close and "adj_close" in df.columns) else "close"
            for row in df.itertuples(index=False):
                # row.date is a python date
                d = getattr(row, "date")
                p = float(getattr(row, price_col))
                yield d.isoformat(), p
