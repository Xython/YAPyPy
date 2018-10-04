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
        ctx.bc.append(
            Instr("CALL_FUNCTION", 1,
                  lineno=node.lineno))  # AssertError(<arg>) , awalys 1
    ctx.bc.append(Instr("RAISE_VARARGS", 1,
                        lineno=node.lineno))  # <argc> awalys 1
    ctx.bc.append(label)


@py_emit.case(ast.Try)
def py_emit(node: ast.Try, ctx: Context):
    """
    title: try
    test:
    >>> try:
    >>>     a = b
    >>> except:
    >>>     a = 2
    """
    lineno = node.lineno
    bodys = node.body
    handlers = node.handlers
    orelse = node.orelse # wait
    finalbody = node.finalbody # wait
    setup_forward = Label()
    try_forward = Label()
    except_forward = Label()
    ctx.bc.append(Instr("SETUP_EXCEPT", setup_forward))
    for body in bodys:
        py_emit(body, ctx)
    ctx.bc.append( Instr("POP_BLOCK") )
    ctx.bc.append( Instr("JUMP_FORWARD", try_forward))
    ctx.bc.append( setup_forward )
    labels = [Label() for n in range(len(handlers) - 1)]
    print( labels )
    for (idx,handler) in enumerate(handlers):
        h_lineno = handler.lineno
        typ = handler.type
        name = handler.name
        h_bodys = handler.body
        if typ:
            if idx > 0:
                dur_top = labels.pop()
                ctx.bc.append( dur_top )
            ctx.bc.append( Instr("DUP_TOP") )
            py_emit(typ, ctx)
            ctx.bc.append( Instr("COMPARE_OP",Compare.EXC_MATCH) )
            if labels:
                ctx.bc.append( Instr("POP_JUMP_IF_FALSE",labels[-1] ) )
            else:
                ctx.bc.append( Instr("POP_JUMP_IF_FALSE",except_forward) )
        ctx.bc.append ( Instr("POP_TOP") )
        if name:
            name_forward = Label()
            ctx.store_name( name )
            ctx.bc.append ( Instr("POP_TOP") )
            ctx.bc.append ( Instr("SETUP_FINALLY", name_forward) )
        else:
            ctx.bc.append ( Instr("POP_TOP") )
            ctx.bc.append ( Instr("POP_TOP") )
        for hbody in h_bodys:
            py_emit(hbody, ctx)
        #ctx.bc.append( Instr("POP_EXCEPT") )
        if name:
            ctx.bc.append( Instr("POP_BLOCK") )
            ctx.bc.append( Instr("LOAD_CONST",None) )
            ctx.bc.append( name_forward )
            ctx.bc.append( Instr("LOAD_CONST",None) )
            ctx.store_name( name )
            ctx.del_name( name )
        ctx.bc.append( Instr("POP_EXCEPT") )
        ctx.bc.append( Instr("JUMP_FORWARD", except_forward) )
    ctx.bc.append( try_forward )    
    ctx.bc.append( Instr("END_FINALLY") )
    ctx.bc.append( except_forward )
    # process else 