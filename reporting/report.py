import typing
import pandas as pd

from reporting.reporter import EmailReporter


def generateReport(data: typing.Mapping[str, pd.DataFrame]):
    """
    :param data: mapping of asset_id to its signal data frame
    :return:
    """
    df = pd.concat(data, axis=1)
    signals = df.xs('signal', axis=1, level=1)
    ### email the following detail
    emailReporter = EmailReporter(['quantpiece+test@gmail.com'])
    emailReporter.send(signals.tail(10).sort_index(ascending=False))
    return signals

if __name__=='__main__':
    test_df = pd.DataFrame([[1,2,3], [4,5,6]], columns=['a', 'b', 'c'])
    emailReporter = EmailReporter(['quantpiece+test@gmail.com'])
    emailReporter.send(test_df.tail(10).sort_index(ascending=False))
