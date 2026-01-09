import json
import logging

from evaluation import evaluate
from market_data import fetchMarketData
import datetime
import pandas as pd
import typing
from models import Strategy, EvaluationPeriod
from reporting.report import generateReport
from settings import Setting
from strategies.strategy_factory import StrategyFactory
from utils import get_logger
from collections import ChainMap

logger = get_logger(__name__, logging.INFO)

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
    stratIds = assetQuery('Asset', asset_id, ['viable_strategies'])
    viableStrategies = stratQuery('Strategy', stratIds)
    return viableStrategies

def strategy_runner(assetId: str, data: pd.DataFrame) -> typing.Mapping[str, pd.DataFrame]:
    '''
    Execute strategies on a particular asset
    :param data: mapping from assetId to its market data
    :return:
    '''
    viableStrategies: typing.List[Strategy] = getViableStrategy(assetId)
    # TODO: parallelize the for loop below
    results = [{strat.id: StrategyFactory.getStrategy(strat.id, strat.name, **strat.params) \
                .run(data)}
               for strat in viableStrategies]
    names = list()
    if results:
        names = list(list(results[0].values())[0].columns.names)
    results_dict = dict(ChainMap(*results))
    df = pd.concat(results_dict, axis=1, names=['StrategyId'] + names)
    return df

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
    # TODO: apply parallelized version, results should maintain order as input partitions
    results = [func(*params) for params in partitions]
    return results

if __name__=='__main__':
    # TODO: create Setting object and Context object
    settings = Setting.get()
    config = json.loads(open(settings.account_config_path).read())
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
    evaluationPeriods = ['THIRTY_DAYS', 'NINETY_DAYS', 'ONE_YEAR', 'TEN_YEARS']
    endDate = datetime.datetime.now().date()
    timedeltaPeriods = [EvaluationPeriod.fromString(period) for period in evaluationPeriods]
    #####
    for timedeltaPeriod in timedeltaPeriods:
        startDate = endDate - timedeltaPeriod.toTimeDelta()
        ### from here on out, it's asset independent
        data = {asset: fetchMarketData(asset, startDate, endDate) for asset in asset_ids}
        results = parallelized_call(strategy_runner, list(data.items())) # results order is guaranteed by parallelized_call
        # evaluation
        for assetId, result in zip(asset_ids, results):
            strategyIds = list(set(result.columns.get_level_values('StrategyId')))
            [evaluate(assetId, strategyId, result.xs(strategyId, axis=1), evaluationPeriod=timedeltaPeriod)
             for strategyId in strategyIds]
        names = list()
        # if results:
        #     names = list(list(results[0].values())[0].columns.names)
        # results_dict = dict(ChainMap(*results))
        # results_df = pd.concat(results_dict, axis=1, names=['AssetId']+names)
    # res = generateReport(results_df)
    # print(res)