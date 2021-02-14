from evaluation import evaluate
from indicators import IndicatorRunner
from indicators.indicators_impl import MovingWindow
from strategies.strategy_interface import Strategy
import pandas as pd
import numpy as np
import typing

class ThreeHeadStrategyImpl(Strategy):
    ma_type: str # type of moving average, in list ['SMA', 'EMA']
    cur_window_size: int # shortest window size to calculate moving average
    ceil_window_size: int # middle-sized window size to calculate moving average
    floor_window_size: int # longest window size to calculate moving average
    short_allowed: bool # whether short selling is allowed, default is False

    def __init__(self, id:str, **kwargs):
        """
        :param kwargs: including the following attributes
        """
        super().__init__(id, **kwargs)
        assert(self.cur_window_size < self.ceil_window_size < self.floor_window_size)
        self.indicators = [
            MovingWindow(['Adj Close'], ['cur'], window_size=self.cur_window_size, aggregate='mean'),
            MovingWindow(['Adj Close'], ['ceil'], window_size=self.ceil_window_size, aggregate='mean'),
            MovingWindow(['Adj Close'], ['floor'], window_size=self.floor_window_size, aggregate='mean')
        ]

    def __calculateIndicators(self, data: pd.DataFrame):
        data = IndicatorRunner().run(data, self.indicators)
        return data

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
        ### actual strategy ###
        df['position'] = np.where((df['cur'] > df['ceil']) & (df['ceil'] > df['floor']), 1, 0)
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