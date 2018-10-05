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
    byte_codes: list = ctx.bc

    label = Label()
    py_emit(test, ctx)
    byte_codes.append(POP_JUMP_IF_TRUE(label, lineno=node.lineno))

    # calc msg and
    byte_codes.append(LOAD_GLOBAL("AssertionError", lineno=node.lineno))
    if msg is not None:
        py_emit(msg, ctx)
        byte_codes.append(CALL_FUNCTION(
            1,
            lineno=node.lineno,
        ), )  # AssertError(<arg>) , awalys 1
    byte_codes.append(RAISE_VARARGS(1, lineno=node.lineno))  # <argc> awalys 1
    byte_codes.append(label)


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

    byte_codes: list = ctx.bc

    if finalbody is not None:
        finally_forward = Label()
        byte_codes.append(SETUP_FINALLY(finally_forward, lineno=lineno))

    byte_codes.append(SETUP_EXCEPT(setup_forward, lineno=lineno))
    for body in bodys:
        py_emit(body, ctx)
    byte_codes.append(POP_BLOCK())
    byte_codes.append(JUMP_FORWARD(try_forward))
    byte_codes.append(setup_forward)
    labels = [Label()] * len(handlers)

    for (idx, handler) in enumerate(handlers):
        h_lineno = handler.lineno
        typ = handler.type
        name = handler.name
        h_bodys = handler.body

        if typ is not None:
            if idx > 0:
                dur_top = labels.pop()
                byte_codes.append(dur_top)
            byte_codes.append(DUP_TOP())
            py_emit(typ, ctx)
            byte_codes.append(COMPARE_OP(Compare.EXC_MATCH, lineno=h_lineno))
            if labels:
                byte_codes.append(POP_JUMP_IF_FALSE(labels[-1]))
            else:
                byte_codes.append(POP_JUMP_IF_FALSE(endfinally_forward))

        byte_codes.append(POP_TOP(lineno=h_lineno))
        if name is not None:
            name_forward = Label()
            ctx.store_name(name)
            byte_codes.append(POP_TOP())
            byte_codes.append(SETUP_FINALLY(name_forward))
        else:
            byte_codes.append(POP_TOP())
            byte_codes.append(POP_TOP())

        for hbody in h_bodys:
            py_emit(hbody, ctx)
        # byte_codes.append( POP_EXCEPT( ) )
        if name is not None:
            byte_codes.append(POP_BLOCK())
            byte_codes.append(LOAD_CONST(None))
            byte_codes.append(name_forward)
            byte_codes.append(LOAD_CONST(None))
            ctx.store_name(name)
            ctx.del_name(name)
            byte_codes.append(END_FINALLY())

        byte_codes.append(POP_EXCEPT())
        byte_codes.append(JUMP_FORWARD(except_forward))

    byte_codes.append(endfinally_forward)
    byte_codes.append(END_FINALLY())
    byte_codes.append(try_forward)

    for els in orelse:
        py_emit(els, ctx)

    byte_codes.append(except_forward)
    if finalbody is not None:
        byte_codes.append(POP_BLOCK())
        byte_codes.append(LOAD_CONST(None))
        byte_codes.append(finally_forward)
        for elt in finalbody:
            py_emit(elt, ctx)
        byte_codes.append(END_FINALLY())
