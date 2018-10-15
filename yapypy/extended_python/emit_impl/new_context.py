from yapypy.extended_python.pybc_emit import *
from bytecode import dump_bytecode


def emit_function(node: typing.Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda],
                  new_ctx: Context, is_async: bool):
    """
        https://docs.python.org/3/library/dis.html#opcode-MAKE_FUNCTION
        MAKE_FUNCTION flags:
        0x01 a tuple of default values for positional-only and positional-or-keyword parameters in positional order
        0x02 a dictionary of keyword-only parameters’ default values
        0x04 an annotation dictionary
        0x08 a tuple containing cells for free variables, making a closure
        the code associated with the function (at TOS1)
        the qualified name of the function (at TOS)

        """

    parent_ctx: Context = new_ctx.parent
    name = getattr(node, 'name', '<lambda>')
    new_ctx.bc.name = f'{parent_ctx.bc.name}.{name}' if parent_ctx.bc.name else name

    for decorator in getattr(node, 'decorator_list', ()):
        py_emit(decorator, parent_ctx)

    if is_async:
        new_ctx.bc.flags |= CompilerFlags.COROUTINE

    if isinstance(node, ast.Lambda):
        py_emit(node.body, new_ctx)
        new_ctx.bc.append(RETURN_VALUE(lineno=node.lineno))
    else:
        head = node.body
        if isinstance(head, ast.Expr) and isinstance(head.value, ast.Str):
            new_ctx.bc.docstring = head.value.s
        for each in node.body:
            py_emit(each, new_ctx)

    args = node.args
    new_ctx.bc.argcount = len(args.args)
    new_ctx.bc.kwonlyargcount = len(args.kwonlyargs)
    make_function_flags = 0
    if new_ctx.sym_tb.freevars:
        make_function_flags |= 0x08

    if args.defaults:
        make_function_flags |= 0x01

    if args.kw_defaults:
        make_function_flags |= 0x02

    annotations = []
    argnames = []

    for arg in args.args:
        argnames.append(arg.arg)
        if arg.annotation:
            annotations.append((arg.arg, arg.annotation))

    for arg in args.kwonlyargs:
        argnames.append(arg.arg)
        if arg.annotation:
            annotations.append((arg.arg, arg.annotation))
    arg = args.vararg
    if arg:
        new_ctx.bc.flags |= CompilerFlags.VARARGS
        argnames.append(arg.arg)
        if arg.annotation:
            annotations.append((arg.arg, arg.annotation))

    arg = args.kwarg
    if arg:
        new_ctx.bc.flags |= CompilerFlags.VARKEYWORDS
        argnames.append(arg.arg)
        if arg.annotation:
            annotations.append((arg.arg, arg.annotation))

    if any(annotations):
        make_function_flags |= 0x04

    new_ctx.bc.argnames.extend(argnames)

    if make_function_flags & 0x01:
        for each in args.defaults:
            py_emit(each, parent_ctx)
        parent_ctx.bc.append(Instr('BUILD_TUPLE', len(args.defaults), lineno=node.lineno))

    if make_function_flags & 0x02:
        for each in args.kw_defaults:
            py_emit(each, parent_ctx)
        parent_ctx.bc.append(
            Instr('BUILD_TUPLE', len(args.kw_defaults), lineno=node.lineno))

    if make_function_flags & 0x04:
        keys, annotation_values = zip(*annotations)

        for each in annotation_values:
            py_emit(each, parent_ctx)
        parent_ctx.bc.append(Instr('LOAD_CONST', tuple(keys), lineno=node.lineno))

        parent_ctx.bc.append(
            Instr("BUILD_CONST_KEY_MAP", len(annotation_values), lineno=node.lineno))

    if make_function_flags & 0x08:
        new_ctx.load_closure(lineno=node.lineno)

    new_ctx.bc.append(Instr('LOAD_CONST', None))
    new_ctx.bc.append(Instr('RETURN_VALUE'))

    inner_code = new_ctx.bc.to_code()
    parent_ctx.bc.append(Instr('LOAD_CONST', inner_code, lineno=node.lineno))

    # when it comes to nested, the name is not generated correctly now.
    parent_ctx.bc.append(Instr('LOAD_CONST', new_ctx.bc.name, lineno=node.lineno))

    parent_ctx.bc.append(Instr("MAKE_FUNCTION", make_function_flags, lineno=node.lineno))

    parent_ctx.bc.extend(
        [CALL_FUNCTION(1, lineno=node.lineno)] * len(getattr(node, 'decorator_list', ())))

    if isinstance(node, ast.Lambda):
        pass
    else:
        parent_ctx.store_name(node.name, lineno=node.lineno)


@py_emit.case(ast.FunctionDef)
def py_emit(node: ast.FunctionDef, new_ctx: Context):
    """
    title: function def
    prepare:
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> def call(f):
    >>>     return f()
    >>> @call
    >>> def f():
    >>>     return 42
    >>> self.assertEqual(f, 42)
    """
    emit_function(node, new_ctx, is_async=False)


@py_emit.case(ast.AsyncFunctionDef)
def py_emit(node: ast.AsyncFunctionDef, new_ctx: Context):
    emit_function(node, new_ctx, is_async=True)


@py_emit.case(ast.Lambda)
def py_emit(node: ast.Lambda, new_ctx: Context):
    """
    title: lambda
    test:
    >>> print(lambda x: x + 1)
    >>> assert (lambda x: x + 1)(1) == 2
    >>> assert (lambda x: x * 10)(20) == 200
    """
    emit_function(node, new_ctx, is_async=False)


@py_emit.case(ast.ClassDef)
def py_emit(node: ast.ClassDef, ctx: Context):
    """
    title: class
    test:
    >>> class S:
    >>>     pass
    >>> print(S)
    >>> class T(type):
    >>>
    >>>     def __new__(mcs, name, bases, ns):
    >>>         assert name == 'S' and bases == (list, ) and '__module__' in ns and '__qualname__' in ns
    >>>         return type(name, bases, ns)
    >>>
    >>> class S(list, metaclass=T):
    >>>     def get2(self):
    >>>         return self[2]
    >>>
    >>> s = S([1, 2, 3])
    >>> assert s.get2() == 3
    >>> def call(f): return f()
    >>> @call
    >>> class S:
    >>>     def p(self): return 42
    >>> assert S.p == 42
    """
    lineno = node.lineno
    col_offset = node.col_offset
    name = node.name
    parent_ctx: Context = ctx.parent

    ctx.bc.name = f'{parent_ctx.bc.name}.{name}' if parent_ctx.bc.name else name

    for decorator in getattr(node, 'decorator_list', ()):
        py_emit(decorator, parent_ctx)

    head = node.body
    if isinstance(head, ast.Expr) and isinstance(head.value, ast.Str):
        ctx.bc.docstring = head.value.s

    for each in node.body:
        py_emit(each, ctx)

    ctx.bc.argcount = 0
    ctx.bc.kwonlyarbgcount = 0
    ctx.bc.argnames = ['.yapypy.args', '.yapypy.kwargs']

    make_function_flags = 0
    ctx.bc.flags |= CompilerFlags.VARARGS
    ctx.bc.flags |= CompilerFlags.VARKEYWORDS

    if ctx.sym_tb.freevars:
        make_function_flags |= 0x08
        ctx.load_closure(lineno=node.lineno)

    ctx.bc.extend([
        LOAD_GLOBAL('__name__'),
        STORE_FAST('__module__'),
        LOAD_CONST(ctx.bc.name),
        STORE_FAST('__qualname__'),
        LOAD_FAST('.yapypy.kwargs'),
        LOAD_ATTR('get'),
        LOAD_CONST('metaclass'),
        LOAD_GLOBAL('.yapypy.type'),
        CALL_FUNCTION(2),  # get metaclass
        LOAD_CONST(name),
        LOAD_FAST('.yapypy.args'),
        LOAD_GLOBAL('.yapypy.locals'),
        CALL_FUNCTION(0),  # get locals
        DUP_TOP(),
        LOAD_ATTR('pop'),
        DUP_TOP(),
        LOAD_CONST('.yapypy.args'),
        CALL_FUNCTION(1),
        POP_TOP(),
        LOAD_CONST('.yapypy.kwargs'),
        CALL_FUNCTION(1),
        POP_TOP(),
        CALL_FUNCTION(3, lineno=node.lineno),  # create new type
    ])

    ctx.bc.append(Instr('RETURN_VALUE'))
    inner_code = ctx.bc.to_code()

    parent_ctx.bc.append(LOAD_CONST(inner_code, lineno=lineno))
    # when it comes to nested, the name is not generated correctly now.
    parent_ctx.bc.append(LOAD_CONST(name, lineno=lineno))

    parent_ctx.bc.append(MAKE_FUNCTION(make_function_flags, lineno=lineno))

    # *args
    if node.bases:
        vararg = ast.Tuple(node.bases, ast.Load(), lineno=lineno, col_offset=col_offset)
        ast.fix_missing_locations(vararg)
        py_emit(vararg, parent_ctx)
    else:
        parent_ctx.bc.append(LOAD_CONST(()))

    # **kwargs
    if node.keywords:
        keys, values = zip(*[(ast.Str(
            keyword.arg, lineno=keyword.value.lineno, col_offset=keyword.value.
            col_offset) if keyword.arg else None, keyword.value)
                             for keyword in node.keywords])

        ex_dict = ex_ast.ExDict(keys, values, ast.Load())
        ast.fix_missing_locations(ex_dict)
        py_emit(ex_dict, parent_ctx)
    else:
        parent_ctx.bc.append(BUILD_MAP(0))

    parent_ctx.bc.append(CALL_FUNCTION_EX(1))

    parent_ctx.bc.extend(
        [CALL_FUNCTION(1, lineno=lineno)] * len(getattr(node, 'decorator_list', ())))

    parent_ctx.store_name(node.name, lineno=lineno)
