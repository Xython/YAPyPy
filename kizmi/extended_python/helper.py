from rbnf.core.Tokenizer import Tokenizer
from toolz import compose
import ast
import typing as t


class Loc:
    def __matmul__(self, other: t.Union[ast.AST, Tokenizer]):
        return {
            'lineno':
            other.lineno,
            'col_offset':
            other.col_offset if hasattr(other, 'col_offset') else other.colno
        }


loc = Loc()


def _parse_expr(token: Tokenizer):
    expr = ast.parse(token.value).body[0].value
    expr.lineno = token.lineno
    expr.col_offset = token.colno
    return expr


def _value(code: Tokenizer):
    return code.value


def raise_exp(e):
    raise e


def str_maker(*strs: Tokenizer):
    head = strs[0]
    return ast.JoinedStr(**(loc @ head), values=list(map(_parse_expr, strs)))


def atom_expr_rewrite(a: t.Optional[Tokenizer], atom: ast.AST,
                      trailers: t.List[t.Callable[[ast.AST], ast.Suite]]):

    for each in trailers:
        atom = each(atom)

    if a:
        atom = ast.Await(**(loc @ a), value=atom)
    return atom


def split_args_helper(arglist):

    raise NotImplemented


def split_args_helper(arglist):
    return [], []
