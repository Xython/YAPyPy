from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Raise)
def py_emit(node: ast.Raise, ctx: Context):
    """
    title: raise
    prepare:
    >>> def cache_exc(exc_func, handler_func):
    >>>     try:
    >>>         exc_func()
    >>>     except Exception as e:
    >>>         handler_func(e)
    >>> def handler_empty (e):
    >>>     assert isinstance(e,RuntimeError)
    >>> def handler_typeerr (e):
    >>>     assert isinstance(e,TypeError)
    >>> def handler_cause (e):
    >>>     assert isinstance(e,ValueError)
    >>>     assert isinstance(e.__cause__,NameError)

    test:
    >>> def raise_empty ():
    >>>     exec('raise')
    >>> def raise_typeerr ():
    >>>     raise TypeError('typeerror')
    >>> def raise_cause ():
    >>>     raise ValueError('value') from NameError('name')
    >>> cache_exc (raise_empty, handler_empty)
    >>> cache_exc (raise_typeerr, handler_typeerr)
    >>> cache_exc (raise_cause, handler_cause)
    """
    exc = node.exc
    cause = node.cause
    argc = 0
    if exc:
        py_emit(exc, ctx)
        argc += 1
    if cause:
        py_emit(cause, ctx)
        argc += 1
    ctx.bc.append(Instr("RAISE_VARARGS", argc, lineno=node.lineno))


@py_emit.case(ast.Assert)
def py_emit(node: ast.Assert, ctx: Context):
    """
    title: assert
    prepare:
    >>> def cache_exc(exc_func, handler_func):
    >>>     try:
    >>>         exc_func()
    >>>     except Exception as e:
    >>>         handler_func(e)
    >>> def handler_zero (e):
    >>>     assert isinstance(e, AssertionError)

    test:
    >>> def assert_zero ()
    >>>     assert 0,"num is zero"
    >>> cache_exc(assert_zero, handler_zero)
    """
    test = node.test
    msg = node.msg
    label = Label()
    py_emit(test, ctx)
    ctx.bc.append(POP_JUMP_IF_TRUE(label, lineno=node.lineno))

    # calc msg and
    ctx.bc.append(LOAD_GLOBAL("AssertionError", lineno=node.lineno))
    if msg:
        py_emit(msg, ctx)
        ctx.bc.append(CALL_FUNCTION(
            1, lineno=node.lineno))  # AssertError(<arg>) , awalys 1
    ctx.bc.append(RAISE_VARARGS(1, lineno=node.lineno))  # <argc> awalys 1
    ctx.bc.append(label)


@py_emit.case(ast.Try)
def py_emit(node: ast.Try, ctx: Context):
    """
    title: try
    test:
    >>> try:
    >>>     a = b
    >>> except TypeError as e:
    >>>     a = 'type'
    >>> except ValueError as e:
    >>>     a = 'value'
    >>> except NameError as e:
    >>>     a = 'name'
    >>> else:
    >>>     a = 'nothing'
    >>> finally:
    >>>     print( f'current a is:{a!r}')
    >>> assert a == 'name'
    """
    lineno = node.lineno
    bodys = node.body
    handlers = node.handlers
    orelse = node.orelse
    finalbody = node.finalbody
    setup_forward = Label()
    try_forward = Label()
    except_forward = Label()
    endfinally_forward = Label()
    name_forward: Label
    finally_forward: Label

    if finalbody:
        finally_forward = Label()
        ctx.bc.append(SETUP_FINALLY(finally_forward, lineno=lineno))
    ctx.bc.append(SETUP_EXCEPT(setup_forward, lineno=lineno))
    for body in bodys:
        py_emit(body, ctx)
    ctx.bc.append(POP_BLOCK())
    ctx.bc.append(JUMP_FORWARD(try_forward))
    ctx.bc.append(setup_forward)
    labels = [Label() for _ in range(len(handlers) - 1)]

    for (idx, handler) in enumerate(handlers):
        h_lineno = handler.lineno
        typ = handler.type
        name = handler.name
        h_bodys = handler.body
        if typ:
            if idx > 0:
                dur_top = labels.pop()
                ctx.bc.append(dur_top)
            ctx.bc.append(DUP_TOP())
            py_emit(typ, ctx)
            ctx.bc.append(COMPARE_OP(Compare.EXC_MATCH, lineno=h_lineno))
            if labels:
                ctx.bc.append(POP_JUMP_IF_FALSE(labels[-1]))
            else:
                ctx.bc.append(POP_JUMP_IF_FALSE(endfinally_forward))
        ctx.bc.append(POP_TOP(lineno=h_lineno))
        if name:
            name_forward = Label()
            ctx.store_name(name)
            ctx.bc.append(POP_TOP())
            ctx.bc.append(SETUP_FINALLY(name_forward))
        else:
            ctx.bc.append(POP_TOP())
            ctx.bc.append(POP_TOP())
        for hbody in h_bodys:
            py_emit(hbody, ctx)
        #ctx.bc.append( POP_EXCEPT( ) )
        if name:
            ctx.bc.append(POP_BLOCK())
            ctx.bc.append(LOAD_CONST(None))
            ctx.bc.append(name_forward)
            ctx.bc.append(LOAD_CONST(None))
            ctx.store_name(name)
            ctx.del_name(name)
            ctx.bc.append(END_FINALLY())
        ctx.bc.append(POP_EXCEPT())
        ctx.bc.append(JUMP_FORWARD(except_forward))
    ctx.bc.append(endfinally_forward)
    ctx.bc.append(END_FINALLY())
    ctx.bc.append(try_forward)
    for els in orelse:
        py_emit(els, ctx)

    ctx.bc.append(except_forward)
    if finalbody:
        ctx.bc.append(POP_BLOCK())
        ctx.bc.append(LOAD_CONST(None))
        ctx.bc.append(finally_forward)
        for elt in finalbody:
            py_emit(elt, ctx)
        ctx.bc.append(END_FINALLY())
