
from dataclasses import dataclass

@dataclass
class MarketEvent:
    symbol: str
    dt: str
    price: float

@dataclass
class SignalEvent:
    strategy_id: str
    symbol: str
    dt: str
    direction: str  # 'LONG' or 'FLAT'

@dataclass
class OrderEvent:
    strategy_id: str
    symbol: str
    dt: str
    side: str       # 'BUY' or 'SELL'
    qty: int

@dataclass
class FillEvent:
    strategy_id: str
    symbol: str
    dt: str
    side: str
    qty: int
    price: float
    commission: float = 0.0
