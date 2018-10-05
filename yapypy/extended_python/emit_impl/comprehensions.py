from yapypy.extended_python.pybc_emit import *
from bytecode import dump_bytecode


def _call(f):
    return f()


_IsAsync = bool


def _emit_comprehension(ctx: Context,
                        generators: typing.List[ast.comprehension],
                        action) -> typing.Tuple[_IsAsync, ast.expr]:
    labels = []
    is_async_outside = False
    first_iter: ast.expr
    for idx, each in enumerate(generators):
        begin_label, end_label = Label(), Label()
        if each.is_async:
            labels.append((True, begin_label, end_label))
            exc_found, exc_before_final = Label(), Label()
            if idx:
                py_emit(each.iter, ctx)
            else:
                is_async_outside = True
                first_iter = each.iter
                ctx.bc.append(LOAD_FAST('.0'))

            ctx.bc.extend([
                begin_label,
                SETUP_EXCEPT(exc_found),
                GET_ANEXT(),
                LOAD_CONST(None),
                YIELD_FROM(),
            ])
            py_emit(each.target, ctx)
            ctx.bc.extend([
                POP_BLOCK(),
                JUMP_FORWARD(exc_before_final),
                exc_found,
                DUP_TOP(),
                LOAD_GLOBAL("StopAsyncIteration"),
                COMPARE_OP(Compare.EXC_MATCH),
                POP_JUMP_IF_TRUE(end_label),
                END_FINALLY(),
                exc_before_final,
            ])

        else:
            labels.append((False, begin_label, end_label))
            if idx:
                py_emit(each.iter, ctx)
                ctx.bc.append(Instr('GET_ITER'))
            else:
                first_iter = each.iter
                ctx.bc.append(LOAD_FAST(".0"))
            ctx.bc.append(begin_label)
            ctx.bc.append(Instr('FOR_ITER', end_label))
            py_emit(each.target, ctx)
        if each.ifs:
            for if_expr in each.ifs:
                py_emit(if_expr, ctx)
                ctx.bc.append(POP_JUMP_IF_FALSE(begin_label))

    action()
    # is serhiy-storchaka the god of Python?
    # https://github.com/python/cpython/blob/702f8f3611bc49b73772cce2b9b041bd11ff9b35/Python/compile.c

    while labels:
        is_async_block, begin_label, end_label = labels.pop()
        if is_async_block:
            ctx.bc.extend([
                JUMP_ABSOLUTE(begin_label),
                end_label,
                POP_TOP(),
                POP_TOP(),
                POP_TOP(),
                POP_EXCEPT(),
                POP_TOP(),
            ])
        else:
            ctx.bc.extend([
                JUMP_ABSOLUTE(begin_label),
                end_label,
            ])

    return is_async_outside, first_iter


@py_emit.case(ast.DictComp)
def py_emit(node: ast.DictComp, ctx: Context):
    """
    title: dictcomp
    prepare:
    >>> from asyncio import Task, sleep, get_event_loop
    >>> class S:
    >>>   def __init__(self): self.i = 0
    >>>   def __aiter__(self): return self
    >>>   async def __anext__(self):
    >>>        if self.i < 10:
    >>>             self.i += 1
    >>>             await sleep(0.05)
    >>>             return self.i
    >>>        raise StopAsyncIteration

    test:
    >>> print({1: 2 for i in range(10)})
    >>> assert {i:i for i in range(10) if i % 2 if i > 6 } == {7:7, 9:9}
    >>> assert {i:j for i in range(10) if i < 8 for j in range(5) if i % 2 if i > 6 } == {7: 4}
    >>> async def f():
    >>>     return {i: i async for i in S()}
    >>> it = get_event_loop().run_until_complete(f())
    >>> assert it == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
    >>> async def f():
    >>>     return {i: i % 5 async for i in S() if i > 3}
    >>> it = get_event_loop().run_until_complete(f())
    >>> assert it = {4: 4, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 0}
    """

    ctx.bc.argnames.append('.0')

    ctx.bc.argcount = 1
    ctx.bc.append(Instr('BUILD_MAP', 0, lineno=node.lineno))
    parent = ctx.parent

    def delay():
        py_emit(node.value, ctx)
        py_emit(node.key, ctx)
        ctx.bc.append(Instr('MAP_ADD', len(node.generators) + 1))

    is_async_outside, first_iter = _emit_comprehension(ctx, node.generators,
                                                       delay)

    ctx.bc.append(RETURN_VALUE(lineno=node.lineno))

    flags = 0
    if ctx.sym_tb.freevars:
        flags = 0x08
        ctx.load_closure()

    if is_async_outside:
        ctx.bc.flags |= CompilerFlags.COROUTINE

    inner_code = ctx.bc.to_code()
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<dictcomp>'))
    parent.bc.append(MAKE_FUNCTION(flags))

    py_emit(first_iter, parent)
    if is_async_outside:

        @parent.bc.extend
        @_call
        def _():
            return [
                GET_AITER(),
                CALL_FUNCTION(1),
                GET_AWAITABLE(),
                LOAD_CONST(None),
                YIELD_FROM()
            ]

    else:

        @parent.bc.extend
        @_call
        def _():
            return [GET_ITER(), CALL_FUNCTION(1)]


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

    def delay():
        py_emit(node.elt, ctx)
        ctx.bc.append(Instr('SET_ADD', len(node.generators) + 1))

    is_async_outside, first_iter = _emit_comprehension(ctx, node.generators,
                                                       delay)

    ctx.bc.append(RETURN_VALUE(lineno=node.lineno))

    flags = 0
    if ctx.sym_tb.freevars:
        flags = 0x08
        ctx.load_closure()

    if is_async_outside:
        ctx.bc.flags |= CompilerFlags.COROUTINE

    inner_code = ctx.bc.to_code()
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<setcomp>'))
    parent.bc.append(MAKE_FUNCTION(flags))

    py_emit(first_iter, parent)
    if is_async_outside:

        @parent.bc.extend
        @_call
        def _():
            return [
                GET_AITER(),
                CALL_FUNCTION(1),
                GET_AWAITABLE(),
                LOAD_CONST(None),
                YIELD_FROM()
            ]

    else:

        @parent.bc.extend
        @_call
        def _():
            return [GET_ITER(), CALL_FUNCTION(1)]


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

    def delay():
        py_emit(node.elt, ctx)
        ctx.bc.append(Instr('LIST_APPEND', len(node.generators) + 1))

    is_async_outside, first_iter = _emit_comprehension(ctx, node.generators,
                                                       delay)

    ctx.bc.append(RETURN_VALUE(lineno=node.lineno))

    flags = 0
    if ctx.sym_tb.freevars:
        flags = 0x08
        ctx.load_closure()

    if is_async_outside:
        ctx.bc.flags |= CompilerFlags.COROUTINE

    inner_code = ctx.bc.to_code()
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<listcomp>'))
    parent.bc.append(MAKE_FUNCTION(flags))

    py_emit(first_iter, parent)
    if is_async_outside:

        @parent.bc.extend
        @_call
        def _():
            return [
                GET_AITER(),
                CALL_FUNCTION(1),
                GET_AWAITABLE(),
                LOAD_CONST(None),
                YIELD_FROM()
            ]

    else:

        @parent.bc.extend
        @_call
        def _():
            return [GET_ITER(), CALL_FUNCTION(1)]


@py_emit.case(ast.GeneratorExp)
def py_emit(node: ast.GeneratorExp, ctx: Context):
    """
    title: gen exp
    prepare:
    >>> from asyncio import sleep, get_event_loop
    >>> class S:
    >>>   def __init__(self):
    >>>         self.i = 0
    >>>   def __iter__(self): return self
    >>>   async def __anext__(self):
    >>>        if self.i < 10:
    >>>             self.i += 1
    >>>             await sleep(0.05)
    >>>             return self.i
    >>>        raise StopAsyncIteration
    >>> def to_t(aiter):
    >>>     async def _():
    >>>         d = []
    >>>         async for each in aiter:
    >>>             d.append(each)
    >>>         return tuple(d)
    >>>     return get_event_loop().run_until_complete(_())

    test:
    >>> print({1: 2 for i in range(10)})
    >>> assert tuple(i for i in range(10) if i % 2 if i > 6) == (7, 9)
    >>> assert tuple((i, j) for i in range(10) if i < 8 for j in  range(5) if i % 2 if i > 6 ) == ((7, 0), (7, 1), (7, 2), (7, 3), (7, 4))
    >>> async def f():
    >>>     return (i async for i in S())
    >>> it = to_t(get_event_loop().run_until_complete(f()))
    >>> assert dict(zip(it, it)) == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
    >>> async def f():
    >>>     return ((i, i % 5) async for i in S() if i > 3)
    >>> it = to_t(get_event_loop().run_until_complete(f()))
    >>> assert tuple(it) == ((4, 4), (5, 0), (6, 1), (7, 2), (8, 3), (9, 4), (10, 0))


    """

    ctx.bc.argnames.append('.0')

    ctx.bc.argcount = 1
    parent = ctx.parent

    def delay():
        py_emit(node.elt, ctx)
        ctx.bc.extend([
            YIELD_VALUE(),
            POP_TOP(),
        ])

    is_async_outside, first_iter = _emit_comprehension(ctx, node.generators,
                                                       delay)

    ctx.bc.extend([
        LOAD_CONST(None),
        RETURN_VALUE(lineno=node.lineno),
    ])

    flags = 0
    if ctx.sym_tb.freevars:
        flags = 0x08
        ctx.load_closure()

    if is_async_outside:
        ctx.bc.flags |= CompilerFlags.ASYNC_GENERATOR

    inner_code = ctx.bc.to_code()
    parent.bc.append(LOAD_CONST(inner_code))
    parent.bc.append(LOAD_CONST(f'{ctx.bc.name}.<locals>.<genexp>'))
    parent.bc.append(MAKE_FUNCTION(flags))

    py_emit(first_iter, parent)
    if is_async_outside:

        @parent.bc.extend
        @_call
        def _():
            return [
                GET_AITER(),
                CALL_FUNCTION(1),
            ]

    else:

        @parent.bc.extend
        @_call
        def _():
            return [GET_ITER(), CALL_FUNCTION(1)]
