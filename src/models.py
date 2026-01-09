import typing
from datetime import timedelta
from enum import Enum, auto

class Strategy:
    id: str
    name: str
    params: typing.Dict

    def __init__(self, id, name, params):
        self.id = id
        self.name = name
        self.params = params

    def run(self, data):
        pass

class EvaluationPeriod(Enum):
    THIRTY_DAYS = auto() # default
    NINETY_DAYS = auto()
    ONE_YEAR = auto()
    TEN_YEARS = auto()

    @classmethod
    def fromString(cls, enum_str: str):
        try:
            return EvaluationPeriod[enum_str]
        except KeyError:
            return EvaluationPeriod.THIRTY_DAYS

    def toTimeDelta(self):
        return {
            'THIRTY_DAYS': timedelta(days=30),
            'NINETY_DAYS': timedelta(days=90),
            'ONE_YEAR': timedelta(days=365),
            'TEN_YEARS': timedelta(days=365*10),
        }.get(self.name, timedelta(days = 30))

if __name__=="__main__":
    print(EvaluationPeriod.__members__)
    print(EvaluationPeriod.THIRTY_DAYS.toTimeDelta())