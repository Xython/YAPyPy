import ast
import typing as t


class ExDict(ast.Dict):
    def __init__(self, keys: t.List[ast.expr], values: t.List[ast.expr],
                 ctx: t.Union[ast.Store, ast.Load]):
        super().__init__()
        self.keys = keys
        self.values = values
        self.ctx = ctx

    _fields = ('keys', 'values', 'ctx')
