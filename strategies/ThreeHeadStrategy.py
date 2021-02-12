from strategies.strategy_interface import Strategy


class ThreeHeadStrategyImpl(Strategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, data):
        return data