
# ETF Strategy Skeleton (Extensible)

This repo gives you a production-friendly skeleton to run **one ETF strategy today**, while making it trivial to add more strategies later. It follows an **Adapter + Strategy + Risk + Portfolio** pattern and keeps **virtual capital per strategy** to simulate sub-accounts.

## What you get
- `Strategy` base class + a working `SMAMomentum` strategy
- `Broker` interface + `IBKRAdapter` stub (drop-in for live via IB Gateway/TWS)
- `Portfolio` with **virtual cash** per strategy (risk-isolated sizing)
- `RiskManager` (max position %, max portfolio drawdown)
- `Backtester` that runs on CSV OHLCV
- `SQLite` trade log with `strategy_id` for clean attribution
- CLI to **backtest** or **paper/live trade** (paper is default, IBKR optional)

> Dependencies are standard library only. IBKR live trading requires `ib_insync` (install later).

## Quickstart (Backtest)
```bash
python -m venv .venv && source .venv/bin/activate
pip install pandas numpy pyyaml
python src/main.py backtest --config config/strategy_momentum.yaml --prices data/SPY.csv
```

## Backtest with Yahoo Finance (cached parquet)

This mode fetches historical prices from Yahoo via `pandas_datareader` and caches them under `data/prices/yahoo/` as **parquet partitioned by date**, so subsequent runs reuse the cache.

```bash
pip install pandas numpy pyyaml pandas_datareader pyarrow
python src/main.py backtest --config config/strategy_momentum.yaml --source yahoo --start 2010-01-01 --end 2024-12-31
```

The example runs a 50/200 SMA crossover on `SPY` with virtual capital USD 30k.

## Add a new strategy later
1. Create `src/strategies/my_strategy.py` that subclasses `Strategy`.
2. Add an entry in the YAML config with `strategy_id`, `virtual_cash`, and parameters.
3. (Optional) Spin each strategy as a separate process or keep them in one process with different `strategy_id`s. All trades are tagged in SQLite.

## Live (IBKR) Outline
- Start IB Gateway/TWS.
- Install `ib_insync` and fill your credentials in `config/broker_ibkr.json`.
- Run:
```bash
pip install ib_insync
python src/main.py trade --config config/strategy_momentum.yaml --live --broker ibkr
```
The adapter uses `strategy_id` and `virtual_cash` to size orders even though they share the same IB account.

## Files
- `src/core/*`: framework primitives (Strategy, Broker, Portfolio, Risk, Events)
- `src/strategies/momentum.py`: working reference strategy
- `src/adapters/ibkr.py`: IBKR live/paper adapter (stubbed methods marked)
- `src/backtest/backtester.py`: CSV-driven backtester
- `src/storage/db.py`: SQLite logger
- `config/strategy_momentum.yaml`: example configuration
- `data/SPY.csv`: tiny sample dataset (replace with real history)

---

**Note**: This skeleton is intentionally minimal. Extend as needed (slippage models, commissions, borrow costs, multi-asset universes, etc.).
