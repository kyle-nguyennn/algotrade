
from dataclasses import dataclass
from typing import Dict
from .events import FillEvent

@dataclass
class Position:
    qty: int = 0
    avg_price: float = 0.0

class Portfolio:
    def __init__(self, base_currency: str, virtual_cash: float):
        self.base_currency = base_currency
        self.cash = virtual_cash
        self.equity_peak = virtual_cash
        self.positions: Dict[str, Position] = {}

    def update_from_fill(self, fill: FillEvent):
        pos = self.positions.get(fill.symbol, Position())
        if fill.side == "BUY":
            cost = fill.price * fill.qty + fill.commission
            new_qty = pos.qty + fill.qty
            # Weighted average price (commission excluded from avg for simplicity)
            pos.avg_price = (pos.avg_price * pos.qty + fill.price * fill.qty) / max(new_qty, 1)
            pos.qty = new_qty
            self.cash -= cost
        else:  # SELL
            proceeds = fill.price * fill.qty - fill.commission
            pos.qty -= fill.qty
            if pos.qty == 0:
                pos.avg_price = 0.0
            self.cash += proceeds
        self.positions[fill.symbol] = pos

    def market_value(self, prices: Dict[str, float]) -> float:
        value = self.cash
        for sym, pos in self.positions.items():
            value += pos.qty * prices.get(sym, 0.0)
        return value

    def update_equity_peak(self, equity: float):
        if equity > self.equity_peak:
            self.equity_peak = equity
