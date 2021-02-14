import typing
import pandas as pd

class Strategy:
    def __init__(self, id: str, **kwargs):
        self.id = id
        for k,v in kwargs.items():
            setattr(self, k, v)

    def run(self, data: typing.Mapping[str, pd.DataFrame]) -> pd.DataFrame:
        raise NotImplementedError
