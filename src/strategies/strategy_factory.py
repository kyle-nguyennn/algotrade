from strategy_registry import STRATEGIES

class StrategyFactory:
    @classmethod
    def getStrategy(cls, id, name, **kwargs):
        implCls = STRATEGIES[name].get('implementation_class')
        strategy = implCls(id, **kwargs)
        return strategy