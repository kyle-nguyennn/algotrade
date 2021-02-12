import typing

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
