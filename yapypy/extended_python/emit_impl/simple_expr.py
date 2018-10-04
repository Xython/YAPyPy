from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Num)
def py_emit(node: ast.Num, ctx: Context):
    ctx.bc.append(Instr("LOAD_CONST", node.n, lineno=node.lineno))


@py_emit.case(ast.Set)
def py_emit(node: ast.Set, ctx: Context):
    """
    title: set
    prepare:
    >>>

    test:
    >>> assert {1,2} == {1,2}
    >>> assert {1,*{2,3},*{3,4}} == {1,2,3,4}
    >>> assert {1, *{2, 3, 4}, 6, *{6, 7}, 8} == {1, 2, 3, 4, 6, 7, 8}
    """
    elts = node.elts
    starreds = [ ]
    n = 0
    for elt in elts:
        if isinstance(elt,ast.Starred):
            starreds += [elt]
        else:
            py_emit(elt, ctx)
            n += 1
    ctx.bc.append(BUILD_SET(n, lineno=node.lineno))
    for starred in starreds:
        py_emit(starred.value, ctx)
    ctx.bc.append(Instr("BUILD_SET_UNPACK",len(starreds) + 1
                        ,lineno=node.lineno))


@py_emit.case(ast.Str)
def py_emit(node: ast.Str, ctx: Context):
    ctx.bc.append(LOAD_CONST(node.s, lineno=node.lineno))


@py_emit.case(ast.JoinedStr)
def py_emit(node: ast.JoinedStr, ctx: Context):
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
    test:
    >>> x = [1, 2, 3]
    >>> assert x[::-1] == [3, 2, 1]
    >>> assert x[::-2] == [3, 1]
    >>> assert x[:1:-1] ==  [3]
    >>> assert x[:0:-1] == [3, 2]
    >>> assert x[1:2:1] == [2]
    >>> class S:
    >>>    def __getitem__(self, item):
    >>>         if item == (1, slice(2, 3, None)): return 1
    >>>         elif item == (slice(None, 3, 2), 2): return 2
    >>> assert x[1, 2:3] == 1
    >>> assert x[:3:2, 2] == 2


    """
    slices = [node.lower, node.upper, node.step]
    if not any(slices):
        ctx.bc.append(LOAD_CONST(None))
        ctx.bc.append(LOAD_CONST(None))
        ctx.bc.append(BUILD_SLICE(2))

        return

    n = max([i for i, piece in enumerate(slices) if piece is not None]) + 1
    for each in slices[:n]:
        if not each:
            ctx.bc.append(LOAD_CONST(None))
        else:
            py_emit(each, ctx)
    ctx.bc.append(BUILD_SLICE(n))
