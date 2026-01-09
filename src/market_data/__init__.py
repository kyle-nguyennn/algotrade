"""Market data access layer (fetch + cache + iteration).

This package intentionally exports a legacy-compatible `fetchMarketData` helper
used by older parts of the codebase, but backed by the newer parquet cache.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Union

import pandas as pd

from .prices import YahooPriceStore


@lru_cache(maxsize=16)
def fetchMarketData(asset_id: str, start_date: Union[str, pd.Timestamp], end_date: Union[str, pd.Timestamp]):
	"""Legacy market data accessor.

	Returns a DataFrame shaped like `pandas_datareader.data.get_data_yahoo`:
	- DateTimeIndex named `Date`
	- Columns: Open, High, Low, Close, Volume, Adj Close (when available)

	Under the hood, it uses the parquet cache in `data/prices/yahoo/`.
	"""

	store = YahooPriceStore.default()
	cached = store.load_range(asset_id, start_date, end_date)
	if cached.empty:
		return cached

	df = cached.copy()
	if "date" in df.columns:
		idx = pd.to_datetime(df["date"])
		df = df.drop(columns=["date"], errors="ignore")
	else:
		idx = pd.to_datetime(df.index)

	df.index = idx
	df.index.name = "Date"

	df = df.rename(
		columns={
			"open": "Open",
			"high": "High",
			"low": "Low",
			"close": "Close",
			"adj_close": "Adj Close",
			"volume": "Volume",
		}
	)

	preferred_order = ["Open", "High", "Low", "Close", "Volume", "Adj Close"]
	existing = [c for c in preferred_order if c in df.columns]
	return df[existing].sort_index()
