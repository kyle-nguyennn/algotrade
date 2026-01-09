
from collections import deque
from typing import Optional
from core.strategy import Strategy
from core.events import MarketEvent, SignalEvent

class SMAMomentum(Strategy):
    def __init__(self, strategy_id: str, fast_window: int, slow_window: int, symbol: str, max_position_pct: float):
        super().__init__(strategy_id)
        if fast_window >= slow_window:
            raise ValueError("fast_window must be < slow_window")
        self.fast_w = fast_window
        self.slow_w = slow_window
        self.symbol = symbol
        self.max_position_pct = max_position_pct
        self.fast_q = deque(maxlen=fast_window)
        self.slow_q = deque(maxlen=slow_window)
        self.prev_state = "FLAT"

    def on_bar(self, bar: MarketEvent) -> Optional[SignalEvent]:
        if bar.symbol != self.symbol:
            return None
        self.fast_q.append(bar.price)
        self.slow_q.append(bar.price)
        if len(self.slow_q) < self.slow_w:
            return None
        fast = sum(self.fast_q)/len(self.fast_q)
        slow = sum(self.slow_q)/len(self.slow_q)
        state = "LONG" if fast > slow else "FLAT"
        sig = None
        if state != self.prev_state:
            sig = SignalEvent(self.strategy_id, self.symbol, bar.dt, state)
        self.prev_state = state
        return sig
