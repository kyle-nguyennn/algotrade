from indicators import Indicator
import pandas as pd

class MovingWindow(Indicator):
    def __init__(self, input_cols, output_cols, **kwargs):
        """
        Calculate the moving aggregate of input_cols and append to data as output_cols
        :param kwargs:
            window_size: int
            aggregate: str
                Aggregate function to execute on the window, in list ['mean', 'std', etc.], anything pandas support
        """
        assert(len(input_cols) == len(output_cols))
        self.initial = 'ma'
        self.inputCols = input_cols
        self.outputCols = output_cols
        super().__init__(**kwargs)

    def calculate(self, data: pd.DataFrame):
        data = data[self.inputCols]
        for inputCol, outputCol in zip(self.inputCols, self.outputCols):
            try:
                res = data[inputCol].rolling(self.params['window_size'])
                data[outputCol] = getattr(res, self.params['aggregate'])()
            except Exception:
                print(f"Cannot get attribute {self.params['aggregate']} from {type(res)}.")
        return data[self.outputCols]