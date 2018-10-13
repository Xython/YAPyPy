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
    if node.value:
        py_emit(node.value, ctx)
    else:
        ctx.bc.append(LOAD_CONST(None))
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
            'STORE_ATTR': 'LOAD_ATTR',
        }.get(instr.name)
        return Instr(opname, instr.arg, lineno=instr.lineno)

    target = node.target
    target_ty = type(target)
    py_emit(target, ctx)
    to_move: Instr = ctx.bc.pop()

    if target_ty is ast.Subscript:
        ctx.bc.append(DUP_TOP_TWO())
    elif target_ty is ast.Attribute:
        ctx.bc.append(DUP_TOP())

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

    if target_ty is ast.Subscript:
        rot_instr = ROT_THREE(lineno=node.target.lineno)
        ctx.bc.append(rot_instr)
    elif target_ty is ast.Attribute:
        rot_instr = ROT_TWO(lineno=node.target.lineno)
        ctx.bc.append(rot_instr)

    ctx.bc.append(to_move)


@py_emit.case(ast.AnnAssign)
def py_emit(node: ast.AnnAssign, ctx: Context):
    """
    title: ann_assign
    test:
    >>> lfkdsk : int = 1111111
    >>> assert lfkdsk == 1111111

    >>> d : int = 2000 if lfkdsk == 1111111 else 3000
    >>> assert d == 2000

    >>> a = [1, 3, 5]
    >>> a[1] : int = 1000
    >>> assert a[1] == 1000

    >>> def fun(x : int):
    >>>     return x
    >>> assert fun(100) == 100

    >>> s : dict = dict()
    >>> assert s is not None
    >>> i: int
    >>> assert 'i' not in locals()
    >>> assert 'i' in locals().get('__annotations__')
    >>> def fun():
    >>>     c : int
    >>>     assert 'c' not in locals()
    >>>     assert locals().get('__annotations__') is None
    >>> fun()
    >>> class B:
    >>>     d : int
    >>>     assert 'd' not in locals()
    >>>     assert 'd' in locals().get('__annotations__')
    >>> B()
    """

    def save_annotation(code, name):
        if sys.version_info < (3, 7):
            code.append(STORE_ANNOTATION(name.id, lineno=name.lineno))
        else:
            code.extend([
                Instr('LOAD_NAME', '__annotations__'),
                LOAD_CONST(name.id),
                STORE_SUBSCR()
            ])

    byte_code: list = ctx.bc
    target = node.target
    value = node.value
    cts = ctx.cts

    value_is_none = value is None
    class_or_module = {ContextType.ClassDef, ContextType.Module}
    should_save_annotation = False
    target_type = type(target)

    if cts is not None:
        under_class_of_module = bool(class_or_module & cts)
        is_global_context = ctx.is_global
        should_save_annotation = under_class_of_module or is_global_context

    if value_is_none:
        if should_save_annotation:
            py_emit(node.annotation, ctx)
            save_annotation(byte_code, target)
        return

    # load value
    py_emit(value, ctx)
    # store target
    py_emit(target, ctx)
    # load annotation
    py_emit(node.annotation, ctx)

    if target_type is ast.Name:
        save_annotation(byte_code, target)
    else:
        byte_code.append(POP_TOP(lineno=target.lineno))
