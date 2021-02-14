import pandas as pd
import logging
import matplotlib.pyplot as plt
import os
from reporting.exporter import PdfExporter
from settings import Setting
from utils import get_logger, get_project_root, get_temp_path
import tempfile
import datetime

logger = get_logger(__name__, logging.INFO)

# TODO: move to settings

def evaluate(df: pd.DataFrame, name: str, deleteTemp=False) -> bool:
    """
    Evaluate the performance of an arbitrary strategy. Columns required in df for evaluation process as below
    :param
        df: assume the existence of these columns
            value: unit value of the portfolio
            unit_asset_ret: unit value of the asset
        name: in the format stratId_assetId
        :return:
    """
    if not deleteTemp:
        tempDir = None
        tempPath = get_temp_path()
        if not os.path.exists(tempPath):
            os.makedirs(tempPath)
    else:
        tempDir = tempfile.TemporaryDirectory()
        tempPath = tempDir.name
    graph_file_extension = Setting.get().graph_file_extension
    tempPath = os.path.join(tempPath, name)
    fig = plt.figure(figsize=(15, 10))
    s1 = fig.add_subplot(2, 1, 1)
    s1.plot(df['value'], label='Portfolio unit value')
    s1.plot(df['unit_asset_ret'], label='Asset unit value')
    s1.legend()
    s1.set_title("Return")
    s2 = fig.add_subplot(2, 1, 2)
    alpha = df['value'] - df['unit_asset_ret']
    s2.plot(alpha, label='Excess return compared to asset', color='r')
    s2.legend()
    s2.set_title("Alpha")
    fig.savefig(tempPath + f'.{graph_file_extension}', format=graph_file_extension)
    logger.info(f"Graph for {name} generated at {tempPath}.")
    if tempDir: tempDir.cleanup()
    ### TODO: define the criteria for a pass
    return True