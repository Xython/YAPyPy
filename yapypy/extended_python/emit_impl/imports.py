from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Import)
def py_emit(node: ast.Import, ctx: Context):
    """
    title: import
    test:
    >>> import os as os, sys
    """
    byte_code: list = ctx.bc
    for name in node.names:
        byte_code.append(
            Instr(
                "LOAD_CONST",
                0,
                lineno=node.lineno,
            ),
        )  # TOS1 for level, default to zero
        byte_code.append(
            Instr(
                "LOAD_CONST",
                None,
                lineno=node.lineno,
            ),
        ),  # TOS for fromlist()
        byte_code.append(Instr("IMPORT_NAME", name.name, lineno=node.lineno))
        as_name = name.asname or name.name
        ctx.store_name(as_name, lineno=node.lineno)


@py_emit.case(ast.ImportFrom)
def py_emit(node: ast.ImportFrom, ctx: Context):
    """
    title: import from
    test:
     >>> from os.path import join
     >>> from os import path as _path
     >>> from os import *
     >>> from os.path import *
     >>> def f(x):
     >>>     x
     >>> print(_path)
     >>> print(join('a', 'b'))
     >>> print(f(1))
     >>> x, y = 1, 2
     >>> print(x, y)
    """
    lineno = node.lineno

    ctx.bc.append(Instr("LOAD_CONST", node.level, lineno=lineno))
    names = tuple(name.name for name in node.names)
    ctx.bc.append(LOAD_CONST(names, lineno=lineno))
    ctx.bc.append(Instr("IMPORT_NAME", node.module, lineno=lineno))

    if names == ('*', ):
        ctx.bc.append(Instr('IMPORT_STAR', lineno=lineno))

    else:
        for name in node.names:
            ctx.bc.append(Instr("IMPORT_FROM", name.name, lineno=lineno))
            as_name = name.asname or name.name
            ctx.store_name(as_name, lineno=lineno)
        ctx.bc.append(POP_TOP(lineno=lineno))
