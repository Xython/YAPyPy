from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.YieldFrom)
def py_emit(node: ast.YieldFrom, ctx: Context):
    """
    title: yield from
    test:
    >>> def f():
    >>>   yield from 1,
    >>> assert next(f()) == 1
    """
    flags = ctx.bc.flags
    if flags & CompilerFlags.COROUTINE or flags & CompilerFlags.ASYNC_GENERATOR:
        exc = SyntaxError()
        exc.lineno = node.lineno
        exc.msg = 'yield from in async function.'
        raise exc

    ctx.bc.flags |= CompilerFlags.GENERATOR
    append = ctx.bc.append
    py_emit(node.value, ctx)
    append(Instr('GET_YIELD_FROM_ITER', lineno=node.lineno))
    append(Instr('LOAD_CONST', None, lineno=node.lineno))
    append(Instr("YIELD_FROM", lineno=node.lineno))


@py_emit.case(ast.Await)
def py_emit(node: ast.Await, ctx: Context):
    """
        title: await
        prepare:
        >>> from time import sleep as ssleep
        test:
        >>> from asyncio import sleep, Task, get_event_loop
        >>> async def f():
        >>>   await sleep(0.2)
        >>>   return 42
        >>> result = get_event_loop().run_until_complete(f())
        >>> print(result)
        """

    if not (ctx.bc.flags & CompilerFlags.ASYNC_GENERATOR
            or ctx.bc.flags & CompilerFlags.COROUTINE):
        exc = SyntaxError()
        exc.lineno = node.lineno
        exc.msg = 'await outside async function.'
        raise exc
    if ctx.bc.flags | CompilerFlags.ASYNC_GENERATOR:
        pass
    else:
        ctx.bc.flags |= CompilerFlags.COROUTINE

    append = ctx.bc.append
    py_emit(node.value, ctx)
    append(Instr('GET_AWAITABLE', lineno=node.lineno))
    append(Instr('LOAD_CONST', None, lineno=node.lineno))
    append(Instr("YIELD_FROM", lineno=node.lineno))


@py_emit.case(ast.Yield)
def py_emit(node: ast.Yield, ctx: Context):
    """
    title: yield
    prepare:
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> def f():
    >>>     yield 1
    >>> self.assertEqual(1, next(f()))
    """
    if ctx.bc.flags & CompilerFlags.COROUTINE:
        if ctx.bc.flags & CompilerFlags.GENERATOR:
            ctx.bc.flags ^= CompilerFlags.GENERATOR

        ctx.bc.flags ^= CompilerFlags.COROUTINE
        ctx.bc.flags |= CompilerFlags.ASYNC_GENERATOR
    elif ctx.bc.flags & CompilerFlags.ASYNC_GENERATOR:
        pass
    else:
        ctx.bc.flags |= CompilerFlags.GENERATOR

    py_emit(node.value, ctx)
    ctx.bc.append(Instr('YIELD_VALUE', lineno=node.lineno))
