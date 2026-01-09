
from abc import ABC, abstractmethod
from typing import Optional
from .events import OrderEvent, FillEvent

class Broker(ABC):
    @abstractmethod
    def place_order(self, order: OrderEvent) -> Optional[FillEvent]:
        pass

class PaperBroker(Broker):
    def __init__(self, slippage_bps: float = 0.0, commission: float = 0.0):
        self.slippage_bps = slippage_bps
        self.commission = commission

    def place_order(self, order: OrderEvent) -> Optional[FillEvent]:
        # Fill at market with optional slippage/commission
        price = getattr(order, "price", None) or 0.0
        # In backtest we set price at bar close; at trade we need L1 quote.
        # Here, assume caller attaches price in the OrderEvent as attribute.
        exec_price = price * (1 + (self.slippage_bps/10000.0) * (1 if order.side == "BUY" else -1))
        return FillEvent(
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            dt=order.dt,
            side=order.side,
            qty=order.qty,
            price=exec_price,
            commission=self.commission
        )
