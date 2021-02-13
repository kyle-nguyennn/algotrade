import pandas as pd

def evaluate(df: pd.DataFrame) -> bool:
    """
    Evaluate the performance of an arbitrary strategy. Columns required in df for evaluation process as below
    :param df: assume the existence of these columns
        value: unit value of the portfolio
        unit_asset_ret: unit value of the asset
    :return:
    """
    df[['value', 'unit_asset_ret']].plot()
    alpha = df['value'] - df['unit_asset_ret']
    alpha.plot()
    ### TODO: define the criteria for a pass
    return True