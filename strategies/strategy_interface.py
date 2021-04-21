import typing
import pandas as pd
import numpy as np

from evaluation import evaluate
from indicators import IndicatorRunner


class Strategy:
    '''
        id: str - an id of the strategy with a unique set of parameter
        indicators: list[Indicator] - list of indicators needed to calculate position at time t
    '''
    def __init__(self, id: str, **kwargs):
        self.id = id
        self.indicators = None
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __calculateIndicators(self, data: pd.DataFrame):
        if self.indicators == None:
            raise NotImplementedError("Child class must define self.indicators.")
        data = IndicatorRunner().run(data, self.indicators)
        return data

    def calculatePosition(self, df: pd.DataFrame):
        raise NotImplementedError("Child class must define specific logic to attain a position.")

    def run(self, data: typing.Mapping[str, pd.DataFrame]) -> pd.DataFrame:
        """
        :param data:
        :return: a series of buy/sell signal
        """
        ### this step should be implemented in Indicator class
        assetId = list(data.keys())[0]
        df = data[assetId]
        df = df.dropna()
        ### enrich data required for strategy implementation
        df = self.__calculateIndicators(df)
        ### actual strategy - logic defined in child class ###
        df['position'] = self.calculatePosition(df)
        ### evaluation parameters
        df['asset_ret'] = df['Adj Close'].pct_change()
        df['return'] = df['asset_ret'] * df['position']
        df['unit_asset_ret'] = (1 + df['asset_ret']).cumprod()
        df['value'] = (1 + df['return']).cumprod()
        ### evaluate
        evalName = f"{self.id}_{assetId}"
        if not evaluate(df, evalName):
            print(f"Strategy {self.__name__} is not suitable for this asset [{assetId}].")
            return None
        ### generate buy/sell signal if pass evaluation phase
        """
            signal: in list ['BUY', 'SELL', 'HOLD']
        """
        df['signal'] = np.where((df['position'] == 1) & (df['position'].shift(1) == 0), 'BUY', 'HOLD')
        df['signal'] = np.where((df['position'] == 0) & (df['position'].shift(1) == 1), 'SELL', df['signal'])
        df['signal'] = df['signal'] + '-' + df['Adj Close'].apply("{0:.2f}".format)
        return df
