import ast
import typing as t


class ExDict(ast.Dict):
    def __init__(self,
                 keys: t.List[ast.expr],
                 values: t.List[ast.expr],
                 ctx: t.Union[ast.Store, ast.Load],
                 lineno=None,
                 col_offset=None):
        super().__init__()
        self.keys = keys
        self.values = values
        self.ctx = ctx
        if lineno:
            self.lineno = lineno
        if col_offset:
            self.col_offset = col_offset

    _fields = ('keys', 'values', 'ctx')
