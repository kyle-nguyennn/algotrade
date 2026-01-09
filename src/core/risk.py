
class RiskManager:
    def __init__(self, max_single_position_pct: float, max_drawdown_pct: float):
        self.max_pos_pct = max_single_position_pct
        self.max_dd_pct = max_drawdown_pct
        self.trading_halted = False

    def check_drawdown(self, equity: float, equity_peak: float):
        if equity_peak <= 0:
            return
        dd = 1 - (equity / equity_peak)
        if dd >= self.max_dd_pct:
            self.trading_halted = True

    def max_position_value(self, virtual_cash: float) -> float:
        return self.max_pos_pct * virtual_cash
