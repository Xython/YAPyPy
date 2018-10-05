from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Return)
def py_emit(node: ast.Return, ctx: Context):
    """
    title: return
    prepare:
    test:
    >>> def f():
    >>>     return 1
    >>> assert f() == 1
    """
    py_emit(node.value, ctx)
    ctx.bc.append(Instr('RETURN_VALUE', lineno=node.lineno))


@py_emit.case(ast.Pass)
def py_emit(node: ast.Pass, ctx: Context):
    pass


@py_emit.case(ast.Nonlocal)
def py_emit(_1, _2):
    pass


@py_emit.case(ast.Global)
def py_emit(_1, _2):
    pass


@py_emit.case(ast.Delete)
def py_emit(node: ast.Delete, ctx: Context):
    for each in node.targets:
        py_emit(each, ctx)


@py_emit.case(ast.Assign)
def py_emit(node: ast.Assign, ctx: Context):
    targets = node.targets
    value = node.value
    n = len(targets)
    py_emit(value, ctx)
    for _ in range(n - 1):
        ctx.bc.append(DUP_TOP(lineno=node.lineno))
    for each in targets:
        py_emit(each, ctx)


@py_emit.case(ast.Expr)
def py_emit(node: ast.Expr, ctx: Context):
    py_emit(node.value, ctx)
    ctx.bc.append(POP_TOP(lineno=node.lineno))


@py_emit.case(ast.AugAssign)
def py_emit(node: ast.AugAssign, ctx: Context):
    """
    title: aug_assign
    prepare:
    >>> class S: pass
    test:
    >>> x = 1
    >>> x += 1
    >>> assert  x == 2
    >>> x = [1, 2, 3]
    >>> x[1 + 1] += 2
    >>> assert x[1 + 1]== 5
prepare:
    >>> s = S()
    >>> s.x = 1
    >>> s.x += 1
    >>> assert s.x == 2
    >>> def f(a={}): return a
    >>> f()['a'] = 1
    >>> f()['a'] *= 2
    >>> assert f()['a'] == 2
    """

    def lhs_to_rhs(instr: Instr):
        opname = {
            'STORE_SUBSCR': 'BINARY_SUBSCR',
            'STORE_FAST': 'LOAD_FAST',
            'STORE_DEREF': 'LOAD_DEREF',
            'STORE_GLOBAL': 'LOAD_GLOBAL',
            'STORE_NAME': 'LOAD_NAME',
            'STORE_ATTR': 'LOAD_ATTR'
        }[instr.name]
        return Instr(opname, instr.arg, lineno=instr.lineno)

    py_emit(node.target, ctx)
    to_move: Instr = ctx.bc.pop()
    is_composed = isinstance(node.target, (ast.Attribute, ast.Subscript))
    if is_composed:
        ctx.bc.append(DUP_TOP_TWO())

    ctx.bc.append(lhs_to_rhs(to_move))
    py_emit(node.value, ctx)
    ctx.bc.append(
        Instr(
            {
                ast.Add: "INPLACE_ADD",
                ast.BitAnd: "INPLACE_AND",
                ast.Sub: "INPLACE_SUBTRACT",
                ast.Div: "INPLACE_TRUE_DIVIDE",
                ast.FloorDiv: "INPLACE_FLOOR_DIVIDE",
                ast.LShift: "INPLACE_LSHIFT",
                ast.RShift: "INPLACE_RSHIFT",
                ast.MatMult: "INPLACE_MATRIX_MULTIPLY",
                ast.Pow: "INPLACE_POWER",
                ast.BitOr: "INPLACE_OR",
                ast.BitXor: "INPLACE_XOR",
                ast.Mult: "INPLACE_MULTIPLY",
                ast.Mod: "INPLACE_MODULO"
            }[type(node.op)],
            lineno=node.lineno))
    if is_composed:
        ctx.bc.append(ROT_THREE(lineno=node.lineno))
    ctx.bc.append(to_move)
