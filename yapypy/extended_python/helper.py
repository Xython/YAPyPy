from rbnf.core.Tokenizer import Tokenizer
import yapypy.extended_python.extended_ast as ex_ast
import ast
import typing as t


class ExprContextFixer(ast.NodeVisitor):
    def __init__(self, ctx):
        self.ctx = ctx

    def _store_simply(self, node):
        node.ctx = self.ctx

    def _store_recursively(self, node):
        node.ctx = self.ctx
        self.generic_visit(node)

    visit_Name = _store_simply
    visit_Subscript = _store_simply
    visit_Attribute = _store_simply
    visit_Tuple = _store_recursively
    visit_List = _store_recursively
    visit_ExDict = _store_recursively
    visit_Starred = _store_recursively


_fix_store = ExprContextFixer(ast.Store()).visit
_fix_del = ExprContextFixer(ast.Del()).visit


class Loc:
    def __matmul__(self, other: t.Union[ast.AST, Tokenizer]):
        return {
            'lineno':
            other.lineno,
            'col_offset':
            other.col_offset if hasattr(other, 'col_offset') else other.colno
        }


class LocatedError(Exception):
    def __init__(self, lineno: int, exc: Exception):
        self.lineno = lineno
        self.exc = exc


loc = Loc()


def as_store(it):
    if hasattr(it, '_fields'):
        _fix_store(it)
        return it
    return it


def as_del(it):
    if hasattr(it, '_fields'):
        _fix_del(it)
        return it
    return it


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


def and_expr_rewrite(head, tail):
    if tail:
        for op, each in tail:
            head = ast.BinOp(head, ast.BitAnd(), each, **loc @ op)
    return head


def arith_expr_rewrite(head, tail):
    if tail:
        for op, each in tail:

            head = ast.BinOp(head, {
                '+': ast.Add,
                '-': ast.Sub
            }[op.value](), each, **loc @ op)
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
            keywords.append(each)
        else:
            positional.append(each)

    return positional, keywords


def def_rewrite(mark: Tokenizer,
                name: Tokenizer,
                args: ast.arguments,
                ret: ast.AST,
                body: list,
                is_async: bool = False):
    name = name.value
    ty = ast.AsyncFunctionDef if is_async else ast.FunctionDef
    return ty(name, args, body, [], ret, **loc @ mark)


def augassign_rewrite(it: Tokenizer):
    return {
        '+=': ast.Add,
        '-=': ast.Sub,
        '*=': ast.Mult,
        '/=': ast.Div,
        '//=': ast.FloorDiv,
        '@=': ast.MatMult,
        '%=': ast.Mod,
        '&=': ast.BitAnd,
        '|=': ast.BitOr,
        '^=': ast.BitXor,
        '<<=': ast.LShift,
        '>>=': ast.RShift,
        '**=': ast.Pow
    }[it.value]


def expr_stmt_rewrite(lhs, ann, aug, aug_exp, rhs: t.Optional[list]):

    if rhs:
        as_store(lhs)
        *init, end = rhs
        for each in init:
            as_store(each)
        return ast.Assign([lhs, *init], end)

    if ann:
        as_store(lhs)
        anno, value = ann
        return ast.AnnAssign(lhs, anno, value, 1)

    if aug_exp:
        as_store(lhs)
        return ast.AugAssign(lhs, aug(), aug_exp)

    # NO AS STORE HERE!
    return ast.Expr(lhs)


def if_stmt_rewrite(marks, tests, bodies, orelse):
    orelse = orelse or []
    head = None
    for mark, test, body, in reversed(tuple(zip(marks, tests, bodies))):
        head = ast.If(test, body, orelse, **loc @ mark)
        orelse = [head]
    return head


def while_stmt_rewrite(test, body, orelse):
    orelse = orelse or []
    return ast.While(test, body, orelse)


def for_stmt_rewrite(target, iter, body, orelse, is_async=False):
    orelse = orelse or []
    as_store(target)
    ty = ast.AsyncFor if is_async else ast.For
    return ty(target, iter, body, orelse)


def try_stmt_rewrite(mark, body, excs, rescues, orelse, final):
    excs = excs or []
    rescues = rescues or []

    def handlers():
        for (type, name), body in zip(excs, rescues):
            yield ast.ExceptHandler(type, name, body)

    return ast.Try(body, list(handlers()), orelse or [], final or [],
                   **loc @ mark)


def with_stmt_rewrite(mark, items, body, is_async=False):
    ty = ast.AsyncWith if is_async else ast.With
    return ty(items, body, **loc @ mark)


def check_call_args(loc, seq: t.List[ast.expr]):
    in_keyword_section = False
    for each in seq:
        if isinstance(each, ast.keyword):
            in_keyword_section = True
        elif in_keyword_section and not isinstance(each, ast.Starred):
            error = SyntaxError()
            error.lineno = loc['lineno']
            error.msg = 'non-keyword argument follows keyword argument'
            raise error
    return seq


def atom_rewrite(loc, name, number, strs, namedc, ellipsis,  dict, is_dict, is_gen, is_list, comp, yield_expr):
    if name:
        return ast.Name(name.value, ast.Load(), **loc @ name)

    if number:
        return ast.Num(eval(number.value), **loc @ number)

    if strs:
        return str_maker(*strs)

    if ellipsis:
        return ast.Ellipsis()

    if namedc:
        return ast.NameConstant(eval(namedc.value), **loc @ namedc)

    if is_dict:
        return dict or ex_ast.ExDict([], [], ast.Load(), **loc @ is_dict)

    if is_gen:
        if yield_expr:
            return yield_expr
        return comp(is_tuple=True) if comp else ast.Tuple([], ast.Load(), **
                                                          loc @ is_gen)

    if is_list:
        return comp(is_list=True) if comp else ast.List([], ast.Load(), **
                                                        loc @ is_list)

    raise TypeError
