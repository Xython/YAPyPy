from yapypy.extended_python.pybc_emit import *


def emit_function(node: typing.Union[ast.AsyncFunctionDef, ast.FunctionDef],
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
    if is_async:
        new_ctx.bc.flags |= CompilerFlags.COROUTINE

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
        parent_ctx.bc.append(
            Instr('BUILD_TUPLE', len(args.defaults), lineno=node.lineno))

    if make_function_flags & 0x02:
        for each in args.kw_defaults:
            py_emit(each, parent_ctx)
        parent_ctx.bc.append(
            Instr('BUILD_TUPLE', len(args.kw_defaults), lineno=node.lineno))

    if make_function_flags & 0x04:
        keys, annotation_values = zip(*annotations)
        parent_ctx.bc.append(
            Instr('LOAD_CONST', tuple(keys), lineno=node.lineno))
        for each in annotation_values:
            py_emit(each, parent_ctx)

        parent_ctx.bc.append(
            Instr("BUILD_TUPLE", len(annotation_values), lineno=node.lineno))

    if make_function_flags & 0x08:
        new_ctx.load_closure(lineno=node.lineno)

    new_ctx.bc.append(Instr('LOAD_CONST', None))
    new_ctx.bc.append(Instr('RETURN_VALUE'))

    inner_code = new_ctx.bc.to_code()

    parent_ctx.bc.append(Instr('LOAD_CONST', inner_code, lineno=node.lineno))

    # when it comes to nested, the name is not generated correctly now.
    parent_ctx.bc.append(Instr('LOAD_CONST', node.name, lineno=node.lineno))

    parent_ctx.bc.append(
        Instr("MAKE_FUNCTION", make_function_flags, lineno=node.lineno))

    parent_ctx.store_name(node.name, lineno=node.lineno)


@py_emit.case(ast.FunctionDef)
def py_emit(node: ast.FunctionDef, new_ctx: Context):
    emit_function(node, new_ctx, is_async=False)


@py_emit.case(ast.AsyncFunctionDef)
def py_emit(node: ast.AsyncFunctionDef, new_ctx: Context):
    emit_function(node, new_ctx, is_async=True)
