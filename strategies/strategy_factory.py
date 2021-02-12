from strategy_registry import STRATEGIES

class StrategyFactory:
    @classmethod
    def getStrategy(cls, name, **kwargs):
        implCls = STRATEGIES[name].get('implementation_class')
        strategy = implCls(**kwargs)
        return strategy