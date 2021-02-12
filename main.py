import json
import pandas_datareader as pdr
import datetime
from multiprocessing import Pool
import pandas as pd
import numpy as np
import typing
from models import Strategy
from strategies.strategy_factory import StrategyFactory

CONFIG_PATH = 'config/myaccount_config.json'

def getViableStrategy(asset_id) -> typing.List[Strategy]:
    '''
    DB access to 'assets' entity, getting the list of viable_strategies
    :param asset_id:
    :return: list of viable strategies
    '''
    ### simulate the DB access for asset strategy mapping
    hardCodedStrat = Strategy('test', '3Head', {
        'ma_type': 'SMA',  # TODO: make Enum
        'short_allowed': False,
        'ceil_window_size': 10,  # -1 for previous day
        'floor_window_size': 21,  # 0 for case of constant boundary,
        'cur_window_size': 3  # 1 for current price
    })
    assetQuery = lambda doc_name, id, attrs: {
        'viable_strategies': ['test']
    }
    stratQuery = lambda doc_name, ids: [hardCodedStrat]
    ########## below part is independent of how to fetch data ########
    stratIds = assetQuery('Asset', asset_id, 'viable_strategies')
    viableStrategies = stratQuery('Strategy', stratIds)
    return viableStrategies

def strategy_runner(data: typing.Mapping[str, pd.DataFrame]):
    '''
    Execute strategies on a particular asset
    :param data:
    :return:
    '''
    try:
        assert(len(data) == 1)
    except Exception:
        print("Invalid input format. Skipping this job.")
    assetId = list(data.keys())[0]
    df = data[assetId]
    viableStrategies: typing.List[Strategy] = getViableStrategy(assetId)
    # TODO: parallelize the for loop below
    results = [StrategyFactory.getStrategy(strat.name, **strat.params).run(df) for strat in viableStrategies]
    return results

def parallelized_call(func, partitions, n_jobs=8):
    '''
    :param func: the function to be executed on partitions
    :param partitions: chunks of data as input for func
    :param n_jobs: the number of parallelized workers
    :return: list of results from workers, should have length == len(partitions)

    Note: can be implemented to submit jobs to distributed computing engine like a Spark cluster.
    For now, just implemented to utilize multicore in the host machine
    '''
    # p = Pool(n_jobs)
    # results = p.map(func, partitions)
    # TODO: apply parallelized version
    results = [func(partition) for partition in partitions]
    return results

if __name__=='__main__':
    # TODO: create Setting object and Context object
    config = json.loads(open(CONFIG_PATH).read())
    # TODO: error handling
    watchlist = list(filter(lambda wl: wl['watchlist_id'] == 'default', config['watchlists']))[0]
    asset_ids = watchlist['assets']
    ''' pass asset ids to Analyzer '''
    # 1. single-asset analyzer
    # 2. multi-asset analyzer
    ''' Analyzer askes Strategy for DataConfig (duration, frequency, parameters, etc.) to specify what to fetch from MarketData/Portfolio '''
    ''' Analyzer gets data from MarketData for these assets '''
    # what information you want ?
    # 1. trading info (price, volume, etc.)
    # 2. company info (BS, news, etc.)
    # assuming we get these config from Strategy
    start_date = datetime.date(2010, 1, 1)
    end_date = datetime.datetime.now().date()
    #####
    df = pdr.data.get_data_yahoo(asset_ids, start=start_date, end=end_date)
    ## swap level to put symbols first as it make sense to refer to each asset independently
    df = df.swaplevel('Attributes', 'Symbols', axis=1)
    df = df.fillna(0)
    ### from here on out, it's asset independent
    data = [{asset: df[asset]} for asset in asset_ids]
    results = parallelized_call(strategy_runner, data)
    print(results)