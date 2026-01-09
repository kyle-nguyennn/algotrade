
import argparse, json, importlib, sys, yaml

from backtest.backtester import run_backtest

def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_strategy(class_name: str):
    if class_name == "SMAMomentum":
        from strategies.momentum import SMAMomentum
        return SMAMomentum
    raise ValueError(f"Unknown strategy class {class_name}")

def cmd_backtest(args):
    cfg = load_config(args.config)
    SClass = load_strategy(cfg["strategy"]["class"])
    strat = SClass(
        strategy_id=cfg["strategy"]["strategy_id"],
        fast_window=cfg["strategy"]["params"]["fast_window"],
        slow_window=cfg["strategy"]["params"]["slow_window"],
        symbol=cfg["strategy"]["params"]["symbol"],
        max_position_pct=cfg["strategy"]["params"]["max_position_pct"],
    )

    if args.source == "csv":
        if not args.prices:
            raise SystemExit("--prices is required when --source=csv")
        price_source = {"type": "csv", "path": args.prices}
    else:
        if not args.start or not args.end:
            raise SystemExit("--start and --end are required when --source=yahoo")
        price_source = {
            "type": "yahoo",
            "start": args.start,
            "end": args.end,
            "batch_days": args.batch_days,
            "prefer_adj_close": args.adj_close,
        }

    results = run_backtest(strat, price_source, cfg["portfolio"], cfg["risk"], cfg["storage"]["sqlite_path"])
    print(json.dumps(results, indent=2))

def cmd_trade(args):
    cfg = load_config(args.config)
    if args.broker == "ibkr":
        print("IBKR live trading is outlined in adapters/ibkr.py. Please implement using ib_insync.")
    else:
        print("Paper trading not implemented in this skeleton's CLI; use backtest to validate first.")

def main():
    parser = argparse.ArgumentParser(description="ETF Strategy Runner")
    subparsers = parser.add_subparsers(dest="command")

    p_bt = subparsers.add_parser("backtest", help="Run backtest (CSV or Yahoo w/ cache)")
    p_bt.add_argument("--config", required=True)
    p_bt.add_argument("--source", choices=["csv", "yahoo"], default="csv")
    p_bt.add_argument("--prices", help="CSV path (required when --source=csv)")
    p_bt.add_argument("--start", help="Start date YYYY-MM-DD (required when --source=yahoo)")
    p_bt.add_argument("--end", help="End date YYYY-MM-DD (required when --source=yahoo)")
    p_bt.add_argument("--batch-days", type=int, default=365, help="Yahoo fetch/cache batch size in days")
    p_bt.add_argument("--adj-close", action="store_true", help="Use adjusted close when available")

    p_tr = subparsers.add_parser("trade", help="Run live/paper trading")
    p_tr.add_argument("--config", required=True)
    p_tr.add_argument("--broker", choices=["paper","ibkr"], default="paper")
    p_tr.add_argument("--live", action="store_true")

    args = parser.parse_args()
    if args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "trade":
        cmd_trade(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
