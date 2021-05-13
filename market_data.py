from functools import lru_cache
import pandas_datareader as pdr


@lru_cache(maxsize=16)
def fetchMarketData(asset_id, start_date, end_date):
    df = pdr.data.get_data_yahoo(asset_id, start=start_date, end=end_date)
    # df = df.dropna()
    return df
