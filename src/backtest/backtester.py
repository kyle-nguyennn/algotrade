
from __future__ import annotations

from typing import Dict, Iterable, Iterator, Optional, Tuple

from core.events import MarketEvent, OrderEvent
from core.portfolio import Portfolio
from core.risk import RiskManager
from core.broker import PaperBroker
from storage import db

from market_data.prices import YahooPriceStore, iter_close_from_csv


def _price_iterator_from_source(
    *,
    source: Dict,
    symbol: str,
) -> Iterator[Tuple[str, float]]:
    stype = (source.get("type") or "csv").lower()
    if stype == "csv":
        path = source.get("path")
        if not path:
            raise ValueError("CSV source requires 'path'")
        return iter_close_from_csv(path)
    if stype == "yahoo":
        start = source.get("start")
        end = source.get("end")
        if not start or not end:
            raise ValueError("Yahoo source requires 'start' and 'end' (YYYY-MM-DD)")
        batch_days = int(source.get("batch_days") or 365)
        prefer_adj_close = bool(source.get("prefer_adj_close") or False)
        store = YahooPriceStore.default()
        return store.iter_close_prices(
            symbol,
            start,
            end,
            batch_days=batch_days,
            prefer_adj_close=prefer_adj_close,
        )
    raise ValueError(f"Unknown price source type: {stype}")


def run_backtest(strategy, price_source: Dict, portfolio_cfg: Dict, risk_cfg: Dict, storage_path: str):
    db.ensure_schema(storage_path)
    port = Portfolio(portfolio_cfg["base_currency"], portfolio_cfg["virtual_cash"])
    risk = RiskManager(risk_cfg["max_single_position_pct"], risk_cfg["max_drawdown_pct"])
    broker = PaperBroker()

    price_iter = _price_iterator_from_source(source=price_source, symbol=strategy.symbol)

    last_price = None

    for dt, price in price_iter:
        last_price = price
        bar = MarketEvent(strategy.symbol, dt, price)
        sig = strategy.on_bar(bar)
        equity = port.market_value({strategy.symbol: price})
        port.update_equity_peak(equity)
        risk.check_drawdown(equity, port.equity_peak)
        if risk.trading_halted:
            break
        if sig:
            if sig.direction == "LONG":
                target_value = portfolio_cfg["virtual_cash"] * strategy.max_position_pct
                current_pos = port.positions.get(strategy.symbol)
                current_value = (current_pos.qty * price) if current_pos else 0.0
                to_invest = max(0.0, target_value - current_value)
                qty = int(to_invest // price)
                if qty > 0:
                    order = OrderEvent(strategy.strategy_id, strategy.symbol, dt, "BUY", qty)
                    setattr(order, "price", price)
                    fill = broker.place_order(order)
                    if fill:
                        port.update_from_fill(fill)
                        db.insert_fill(storage_path, fill.__dict__)
            else:
                current_pos = port.positions.get(strategy.symbol)
                if current_pos and current_pos.qty > 0:
                    order = OrderEvent(strategy.strategy_id, strategy.symbol, dt, "SELL", current_pos.qty)
                    setattr(order, "price", price)
                    fill = broker.place_order(order)
                    if fill:
                        port.update_from_fill(fill)
                        db.insert_fill(storage_path, fill.__dict__)

    final_equity = port.market_value({strategy.symbol: last_price or 0.0})
    return {
        "final_equity": final_equity,
        "cash": port.cash,
        "positions": {k: v.__dict__ for k, v in port.positions.items()}
    }
