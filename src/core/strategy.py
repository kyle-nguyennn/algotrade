
from abc import ABC, abstractmethod
from typing import Optional
from .events import MarketEvent, SignalEvent

class Strategy(ABC):
    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id

    @abstractmethod
    def on_bar(self, bar: MarketEvent) -> Optional[SignalEvent]:
        pass
