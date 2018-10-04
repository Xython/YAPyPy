from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.DictComp)
def py_emit(node: ast.DictComp, ctx: Context):
    """
    title: dictcomp
    test:
    >>> print({1: 2 for i in range(10)})
    >>> assert {i:i for i in range(10) if i % 2 if i > 6 } == {7:7, 9:9}
    >>> assert {i:j for i in range(10) if i < 8 for j in  range(5) if i % 2 if i > 6 } == {7: 4}
    where this
    ```
        assert {i:j for i in range(10) if 3 < i < 8 for j in  range(5) if i % 2 if i > 6 } == {7: 4}
    ```
    would fail now
    """
    ctx.bc.argnames.append('.0')
    ctx.bc.argcount = 1
    ctx.bc.append(Instr('BUILD_MAP', 0, lineno=node.lineno))
    parent = ctx.parent
    first_iter: ast.expr
    labels = []
    for idx, each in enumerate(node.generators):
        pair = begin_label, end_label = Label(), Label()

        if each.is_async:
            raise NotImplemented
        else:
            labels.append(pair)
            if idx:
                py_emit(each.iter, ctx)
                ctx.bc.append(Instr('GET_ITER', lineno=node.lineno))
            else:
                first_iter = each.iter
                ctx.bc.append(LOAD_FAST(".0", lineno=node.lineno))
            ctx.bc.append(begin_label)
            ctx.bc.append(Instr('FOR_ITER', end_label, lineno=node.lineno))
            py_emit(each.target, ctx)
            if each.ifs:
                for if_expr in each.ifs:
                    py_emit(if_expr, ctx)
                    ctx.bc.append(
                        POP_JUMP_IF_FALSE(begin_label, lineno=node.lineno))

    py_emit(node.value, ctx)
    py_emit(node.key, ctx)

    ctx.bc.append(Instr('MAP_ADD', len(node.generators) + 1))

    while labels:
        begin_label, end_label = labels.pop()
        ctx.bc.append(JUMP_ABSOLUTE(begin_label, lineno=node.lineno))
        ctx.bc.append(end_label)

    ctx.bc.append(RETURN_VALUE(lineno=node.lineno))
    flags = 0x08 if ctx.sym_tb.freevars else 0
    if flags & 0x08:
        ctx.load_closure()

    inner_code = ctx.bc.to_code()
    # dis.dis(inner_code)
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<dictcomp>'))
    parent.bc.append(MAKE_FUNCTION(flags))
    py_emit(first_iter, parent)
    parent.bc.append(GET_ITER())
    parent.bc.append(CALL_FUNCTION(1))


@py_emit.case(ast.SetComp)
def py_emit(node: ast.SetComp, ctx: Context):
    """
    title SetComp
    test:
    >>> print({ 2 for i in range(10)})
    >>> assert {i for i in range(10) if i % 2 if i > 6 } == { 7, 9 }
    >>> assert {(i, j) for i in range(10) if i < 8 for j in  range(5) if i % 2 if i > 6 } == {(7, 3), (7, 0), (7, 1), (7, 4), (7, 2)}
    """
    ctx.bc.argnames.append('.0')
    ctx.bc.argcount = 1
    ctx.bc.append(Instr('BUILD_SET', 0))
    parent = ctx.parent
    first_iter: ast.expr
    labels = []
    for idx, each in enumerate(node.generators):
        pair = begin_label, end_label = Label(), Label()
        if each.is_async:
            raise NotImplemented
        else:
            labels.append(pair)
            if (idx):
                py_emit(each.iter, ctx)
                ctx.bc.append(GET_ITER(lineno=node.lineno))
            else:
                first_iter = each.iter
                ctx.bc.append(Instr('LOAD_FAST', ".0", lineno=node.lineno))
                ctx.bc.append(begin_label)
            ctx.bc.append(begin_label)
            ctx.bc.append(Instr('FOR_ITER', end_label, lineno=node.lineno))
            py_emit(each.target, ctx)
            if each.ifs:
                for if_expr in each.ifs:
                    py_emit(if_expr, ctx)
                    ctx.bc.append(
                        POP_JUMP_IF_FALSE(begin_label, lineno=node.lineno))

    py_emit(node.elt, ctx)
    ctx.bc.append(Instr('SET_ADD', len(node.generators) + 1))

    while labels:
        begin_label, end_label = labels.pop()
        ctx.bc.append(JUMP_ABSOLUTE(begin_label, lineno=node.lineno))
        ctx.bc.append(end_label)

    ctx.bc.append(RETURN_VALUE(lineno=node.lineno))
    flags = 0x08 if ctx.sym_tb.freevars else 0
    if flags & 0x08:
        ctx.load_closure()

    inner_code = ctx.bc.to_code()
    # dis.dis(inner_code)
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<setcomp>'))
    parent.bc.append(MAKE_FUNCTION(flags))
    py_emit(first_iter, parent)
    parent.bc.append(GET_ITER())
    parent.bc.append(CALL_FUNCTION(1))


@py_emit.case(ast.ListComp)
def py_emit(node: ast.ListComp, ctx: Context):
    """
    title: ListComp
    prepare:
    >>>
    test:
    >>> assert [i for i in range(10)] == [0,1,2,3,4,5,6,7,8,9]
    >>> assert [(i,j) for i in range(2) for j in range(2)] == [(0, 0), (0, 1), (1, 0), (1, 1)]
    """
    ctx.bc.argnames.append('.0')
    ctx.bc.argcount = 1
    ctx.bc.append(Instr('BUILD_LIST', 0))
    parent = ctx.parent
    first_iter: ast.expr
    labels = []
    for idx, each in enumerate(node.generators):
        pair = begin_label, end_label = Label(), Label()
        if each.is_async:
            raise NotImplemented
        else:
            labels.append(pair)
            if (idx):
                py_emit(each.iter, ctx)
                ctx.bc.append(GET_ITER(lineno=node.lineno))
            else:
                first_iter = each.iter
                ctx.bc.append(Instr('LOAD_FAST', ".0", lineno=node.lineno))
                ctx.bc.append(begin_label)
            ctx.bc.append(begin_label)
            ctx.bc.append(Instr('FOR_ITER', end_label, lineno=node.lineno))
            py_emit(each.target, ctx)
            if each.ifs:
                for if_expr in each.ifs:
                    py_emit(if_expr, ctx)
                    ctx.bc.append(
                        POP_JUMP_IF_FALSE(begin_label, lineno=node.lineno))

    py_emit(node.elt, ctx)
    ctx.bc.append(Instr('LIST_APPEND', len(node.generators) + 1))

    while labels:
        begin_label, end_label = labels.pop()
        ctx.bc.append(JUMP_ABSOLUTE(begin_label, lineno=node.lineno))
        ctx.bc.append(end_label)

    ctx.bc.append(RETURN_VALUE(lineno=node.lineno))
    flags = 0x08 if ctx.sym_tb.freevars else 0
    if flags & 0x08:
        ctx.load_closure()

    inner_code = ctx.bc.to_code()
    # dis.dis(inner_code)
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<setcomp>'))
    parent.bc.append(MAKE_FUNCTION(flags))
    py_emit(first_iter, parent)
    parent.bc.append(GET_ITER())
    parent.bc.append(CALL_FUNCTION(1))
