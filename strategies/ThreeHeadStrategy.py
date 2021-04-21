from indicators.indicators_impl import MovingWindow
from strategies.strategy_interface import Strategy
import pandas as pd
import numpy as np

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

    def calculatePosition(self, df: pd.DataFrame) -> pd.Series:
        '''
        Is called in Strategy.run to obtain 'position' column
        :param df: must already be passed through self.__calculateIndicators to obtain necessary columns
                for the calculation in body
        :return: a series of 0 and 1, indicating how many units we're having at that point in time
        '''
        return np.where((df['cur'] > df['ceil']) & (df['ceil'] > df['floor']), 1, 0)
