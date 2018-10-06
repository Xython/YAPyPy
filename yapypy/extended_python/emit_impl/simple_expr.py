from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Num)
def py_emit(node: ast.Num, ctx: Context):
    ctx.bc.append(Instr("LOAD_CONST", node.n, lineno=node.lineno))


@py_emit.case(ast.Set)
def py_emit(node: ast.Set, ctx: Context):
    """
    title: set
    prepare:
    test:
    >>> assert {1,2} == {1,2}
    >>> assert {1,*{2,3},*{3,4}} == {1,2,3,4}
    >>> assert {1, *{2, 3, 4}, 6, *{6, 7}, 8} == {1, 2, 3, 4, 6, 7, 8}
    """

    elts = node.elts
    starreds = list()
    n = 0

    for elt in elts:
        if isinstance(elt, ast.Starred):
            starreds += [elt]
        else:
            py_emit(elt, ctx)
            n += 1
    ctx.bc.append(BUILD_SET(n, lineno=node.lineno))
    for starred in starreds:
        py_emit(starred.value, ctx)
    ctx.bc.append(
        Instr(
            "BUILD_SET_UNPACK",
            len(starreds) + 1,
            lineno=node.lineno,
        ), )


@py_emit.case(ast.Str)
def py_emit(node: ast.Str, ctx: Context):
    ctx.bc.append(LOAD_CONST(node.s, lineno=node.lineno))


@py_emit.case(ast.JoinedStr)
def py_emit(node: ast.JoinedStr, ctx: Context):
    kinds = {type(each) for each in node.values}
    if ast.Bytes in kinds:
        if len(kinds) > 1:
            exc = SyntaxError()
            exc.msg = 'cannot mix bytes and nonbytes literals'
            exc.lineno = node.lineno
            raise exc
        node.values: typing.List[ast.Bytes]
        bytes_const = b''.join(each.s for each in node.values)
        ctx.bc.append(LOAD_CONST(bytes_const, lineno=node.lineno))
    else:
        for each in node.values:
            py_emit(each, ctx)
        ctx.bc.append(BUILD_STRING(len(node.values), lineno=node.lineno))


@py_emit.case(ast.NameConstant)
def py_emit(node: ast.NameConstant, ctx: Context):
    """
    title: named constant
    test:
    >>> x = True
    >>> x = None
    >>> x = False
    """
    ctx.bc.append(LOAD_CONST(node.value, lineno=node.lineno))


@py_emit.case(ast.Slice)
def py_emit(node: ast.Slice, ctx: Context):
    """
    see more test cases for Subscript
    title: slice
    prepare:
    >>> class S:
    >>>    def __getitem__(self, item):
    >>>         if item == (1, slice(2, 3, None)): return 1
    >>>         elif item == (slice(None, 3, 2), 2): return 2
    test:
    >>> x = [1, 2, 3]
    >>> assert x[::-1] == [3, 2, 1]
    >>> assert x[::-2] == [3, 1]
    >>> assert x[:1:-1] ==  [3]
    >>> assert x[:0:-1] == [3, 2]
    >>> assert x[1:2:1] == [2]
    >>> x = S()
    >>> assert x[1, 2:3] == 1
    >>> assert x[:3:2, 2] == 2
    """
    slices = [node.lower, node.upper, node.step]
    if not any(slices):
        ctx.bc.append(LOAD_CONST(None))
        ctx.bc.append(LOAD_CONST(None))
        ctx.bc.append(BUILD_SLICE(2))
        return

    if slices[-1]:
        n = 3
    else:
        n = 2
    for each in slices[:n]:
        if not each:
            ctx.bc.append(LOAD_CONST(None))
        else:
            py_emit(each, ctx)
    ctx.bc.append(BUILD_SLICE(n))


@py_emit.case(ast.Bytes)
def py_emit(node: ast.Bytes, ctx: Context):
    ctx.bc.append(LOAD_CONST(node.s, lineno=node.lineno))


@py_emit.case(ast.Ellipsis)
def py_emit(node: ast.Ellipsis, ctx: Context):
    ctx.bc.append(LOAD_CONST(..., lineno=node.lineno))
