import typing
import pandas as pd
import os
from reporting.reporter import EmailReporter
from settings import Setting
from utils import get_temp_path

graph_file_extension = Setting.get().graph_file_extension

def getGraphs(columns: pd.MultiIndex):
    index = columns.reorder_levels(['StrategyId', 'AssetId'])
    graphNames = map('_'.join, index.values.tolist())
    basePath = get_temp_path()
    return [os.path.join(basePath, f"{filename}.{graph_file_extension}") for filename in graphNames]

def generateReport(data: pd.DataFrame):
    """
    :param data: mapping of asset_id to its signal data frame
    :return:
    """
    signals = data.xs('signal', axis=1, level='Attributes')
    ### email the following detail
    emailReporter = EmailReporter(['quantpiece+test@gmail.com'])
    attachments = getGraphs(signals.columns)
    emailReporter.send(signals.tail(10).sort_index(ascending=False), attachments=attachments)
    return signals

if __name__=='__main__':
    test_df = pd.DataFrame([[1,2,3], [4,5,6]], columns=['a', 'b', 'c'])
    emailReporter = EmailReporter(['quantpiece+test@gmail.com'])
    emailReporter.send(test_df.tail(10).sort_index(ascending=False))
