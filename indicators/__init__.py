import pandas as pd
import typing

class Indicator:
    def __init__(self, **kwargs):
        self.params = dict()
        for k, v in kwargs.items():
            self.params[k] = v

class IndicatorRunner:
    def __init__(self, cache=False):
        if cache:
            # TODO: implement cache, either memcache or messsage queue
            pass

    def run(cls, data: pd.DataFrame, indicators: typing.List[Indicator]):
        # TODO: parallelize the for loop
        results = [indicator.calculate(data) for indicator in indicators]
        res = pd.concat([data] + results, axis=1)
        return res
