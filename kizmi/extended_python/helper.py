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


def shift_expr_rewrite(head, tail):
    if tail:
        for op, each in tail:
            op = {'>>': ast.RShift, '<<': ast.LShift}[op.value]()
            head = ast.BinOp(head, op, each, **loc @ op)
    return head


def comp_op_rewrite(op: t.Union[Tokenizer, t.List[Tokenizer]]):
    """
    ('<'|'>'|'=='|'>='|'<='|'<>'|'!='|'in'|'not' 'in'|'is'|'is' 'not')
    """
    if isinstance(op, list):
        op = tuple(map(lambda it: it.value, op))
    else:
        op = op.value

    return {
        '<': ast.Lt,
        '>': ast.Gt,
        '==': ast.Eq,
        '>=': ast.GtE,
        '<=': ast.LtE,
        '<>': lambda: raise_exp(NotImplemented),
        '!=': ast.NotEq,
        'in': ast.In,
        ('is', ): ast.Is,
        ('is', 'not'): ast.IsNot,
        ('not', 'in'): ast.NotIn
    }[op]()


def expr_rewrite(head, tail):
    if tail:
        for op, each in tail:
            head = ast.BinOp(head, ast.BitOr(), each, **loc @ op)
    return head


def xor_expr_rewrite(head, tail):
    if tail:
        for op, each in tail:
            head = ast.BinOp(head, ast.BitXor(), each, **loc @ op)
    return head


def and_expr_rewrite(seq):
    return ast.BoolOp(ast.BitAnd(), seq)


def arith_expr_rewrite(head, tail):
    if tail:
        for op, each in tail:
            op = {'+': ast.Add, '-': ast.Sub}[op.value]()
            head = ast.BinOp(head, op, each, **loc @ op)
    return head


def term_rewrite(head, tail):
    if tail:
        for op, each in tail:
            op = {
                '*': ast.Mult,
                '@': ast.MatMult,
                '%': ast.Mod,
                '//': ast.FloorDiv,
                '/': ast.Div
            }[op.value]()
            head = ast.BinOp(head, op, each, **loc @ op)
    return head


def factor_rewrite(mark: Tokenizer, factor, power):

    return power if power else ast.UnaryOp(
        **(loc @ mark),
        op={
            '~': ast.Invert,
            '+': ast.UAdd,
            '-': ast.USub
        }[mark.value](),
        operand=factor)


def split_args_helper(arglist):

    positional = []
    keywords = []
    for each in arglist:
        if isinstance(each, ast.keyword):
            positional.append(each)
        else:
            keywords.append(each)
    return positional, keywords
