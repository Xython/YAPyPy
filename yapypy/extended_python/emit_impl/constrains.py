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

    if ContextType.Coroutine in ctx.cts:
        exc = SyntaxError()
        exc.lineno = node.lineno
        exc.msg = 'yield from in async functions.'
        raise exc
    elif ContextType.Module in ctx.cts:
        exc = SyntaxError()
        exc.lineno = node.lineno
        exc.msg = 'yield from outside functions.'
        raise exc

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

    if ContextType.Coroutine not in ctx.cts:
        exc = SyntaxError()
        exc.lineno = node.lineno
        exc.msg = 'await outside async functions.'
        raise exc

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
    >>> yield None
    """
    if ContextType.Module in ctx.cts:
        exc = SyntaxError()
        exc.lineno = node.lineno
        exc.msg = 'yield outside functions.'
        raise exc

    if node.value is not None:
        py_emit(node.value, ctx)
    else:
        ctx.bc.append(LOAD_CONST(None))

    ctx.bc.append(Instr('YIELD_VALUE', lineno=node.lineno))
