import ast
from Redy.Magic.Pattern import Pattern
from bytecode import *
from bytecode.concrete import FreeVar, CellVar
from bytecode.flags import CompilerFlags


class NonlocalManager:
    def __init__(self, ctx: 'Context'):
        self.ctx = ctx

    def __iadd__(self, name):
        self.ctx.parent += name

    def __contains__(self, name):
        return name in self.ctx.parent


class NestedUpFetchManager:
    __slots__ = ['ctx']

    def __init__(self, ctx: 'Context'):
        self.ctx = ctx

    def __contains__(self, name):
        return name in self.ctx or (self.ctx.parent and
                                    name in self.ctx.parent.available_symbols)


def make_global_ctx():
    return Context(Bytecode(), set(), set(), set(), 0, parent=None)


class Context:
    """
    The context rules for python could be the second difficult part
    in the whole emitter implementation(the most difficult is label offset calculating).

    The behaviour of context inheritance is presented here
    explicitly:

    bytecode:
        Each context holds its own bytecode stack.

    locals:
        Each context holds its own local variables.

    nonlocals:
        Each context holds it own nonlocal variables.
        It donates the writable freevars.

    globals_:
        Each context holds it own globals variables.

        Each global var could be visited in read-only mode
        , while only explicitly marked global vars are writable.

        P.S: when current context is the global one, each global
        var is writable.
        ```
        def f():
            global x
            print(x) # print global var `x`
            x = 1    # okay

        def f():
            print(x) # print global var

        def f():
            x = 1    # now x is local variable

        def f():
            print(x) # print local var `x`, however it's not defined yet.
                     # NameError would be raised.
            x = 1

        ```

    ctx_depth:
        ctx.parent.ctx_depth + 1 = ctx.ctx_depth

    """

    def __init__(self,
                 bytecode: Bytecode,
                 locals: set,
                 nonlocals: set,
                 globals_: set,
                 ctx_depth: int,
                 parent: 'Context' = None):
        self.parent = parent or None
        self.bc = bytecode
        self.locals = locals
        self.nonlocals = nonlocals
        self.globals_ = globals_
        self.ctx_depth = ctx_depth

    def lens(self,
             bc=None,
             locals=None,
             nonlocals=None,
             globals_=None,
             parent=None,
             ctx_depth=None):
        return Context(
            bytecode=bc or self.bc,
            locals=locals or self.locals,
            nonlocals=nonlocals or self.nonlocals,
            globals_=globals_ or self.globals_,
            ctx_depth=ctx_depth or self.ctx_depth,
            parent=parent or self.parent)

    def into(self, name: str):
        ctx = self.lens(
            bc=Bytecode(),
            locals=set(),
            nonlocals=set(),
            globals_=set(),
            ctx_depth=self.ctx_depth + 1,
            parent=self)
        ctx.bc.name = name
        return ctx

    def fix_bytecode(self):
        bc = self.bc
        for each in bc:
            if not isinstance(each, Instr):
                continue
            arg = each.arg
            if not isinstance(arg, FreeVar):
                continue
            name = arg.name

            if name not in bc.freevars and self.ctx_depth > 1:
                bc.freevars.append(name)

    def add_nonlocal(self, nonlocal_name):
        self.nonlocals.add(nonlocal_name)

    def __iadd__(self, name):
        if name in self.nonlocals:
            raise NameError(f'`{name}` is nonlocal .')
        return self.locals.add(name)

    def __contains__(self, name):
        return name in self.locals

    @property
    def available_symbols(self):
        return NestedUpFetchManager(self)

    def load_name(self, node: ast.Name):
        id = node.id
        if id in self:
            if id not in self.bc.cellvars:
                self.bc.append(Instr('LOAD_FAST', id, lineno=node.lineno))
            else:
                self.bc.append(
                    Instr('LOAD_DEREF', CellVar(id), lineno=node.lineno))
            return

        if id in self.available_symbols:
            self.bc.append(
                Instr("LOAD_DEREF", FreeVar(id), lineno=node.lineno))
        else:
            self.bc.append(Instr('LOAD_GLOBAL', id, lineno=node.lineno))

    def store_name(self, node: ast.Name):
        id = node.id
        if id in self:
            if id not in self.bc.cellvars:
                self.bc.append(Instr("STORE_FAST", id, lineno=node.lineno))
            else:
                self.bc.append(
                    Instr('STORE_DEREF', CellVar('id'), lineno=node.lineno))
            return
        if id in self.available_symbols and id in self.nonlocals:
            self.bc.append(
                Instr('STORE_DEREF', FreeVar(id), lineno=node.lineno))
        elif id in self.globals_:
            self.bc.append(Instr("STORE_GLOBAL", id, lineno=node.lineno))
        else:
            raise NameError(f'name `{node.id}` not found.')


@Pattern
def py_expr_emit(node: ast.AST, ctx: Context):
    return type(node)


@Pattern
def py_stmt_emit(node: ast.AST, ctx: Context):

    return type(node)


@py_stmt_emit.case(ast.FunctionDef)
async def py_stmt_emit(node: ast.FunctionDef, ctx: Context):
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
    ctx += node.name

    await ctx.declaring()
    args = node.args
    make_function_flags = 0
    if args.defaults:
        make_function_flags |= 0x01
    if args.kw_defaults:
        make_function_flags |= 0x02

    ## make annotations
    annotations = []
    for arg in args.args:
        if arg.annotation:
            annotations.append((arg.arg, arg.annotation))

    for arg in args.kwonlyargs:
        if arg.annotation:
            annotations.append((arg.arg, arg.annotation))
    arg = args.vararg
    if arg and arg.annotation:
        annotations.append((arg.arg, arg.annotation))

    arg = args.kwarg
    if arg and arg.annotation:
        annotations.append((arg.arg, arg.annotation))

    if any(annotations):
        make_function_flags |= 0x04

    new_ctx = ctx.into(node.name)

    for positional_arg in node.args.args:
        new_ctx += positional_arg.arg

    new_ctx.bc.flags |= CompilerFlags.NEWLOCALS  # always?
    # I didn't find related documents, so this is a tentative workaround.

    if new_ctx.ctx_depth > 1:
        # ctx_depth is 0 => global context
        # ctx_depth is 1 => unnested function
        new_ctx.bc.flags |= CompilerFlags.NESTED
    else:
        # functions that could only be accessed as global variables.
        new_ctx.bc.flags |= CompilerFlags.NOFREE

    raise NotImplemented


@py_expr_emit.case(ast.Name)
def py_expr_emit(node: ast.Name, ctx: Context):
    ctx.load_name(node)


@py_expr_emit.case(ast.Expr)
def py_expr_emit(node: ast.Expr, ctx: Context):
    py_expr_emit(node, ctx)
    ctx.bc.append('POP_TOP')


@py_expr_emit.case(ast.YieldFrom)
def py_expr_emit(node: ast.YieldFrom, ctx: Context):
    append = ctx.bc.append
    py_expr_emit(node.value, ctx)
    append(Instr('GET_YIELD_FROM_ITER', lineno=node.lineno))
    append(Instr('LOAD_CONST', None, lineno=node.lineno))
    append(Instr("YIELD_FROM", lineno=node.lineno))


@py_expr_emit.case(ast.Yield)
def py_expr_emit(node: ast.Yield, ctx: Context):
    py_expr_emit(node.value)
    ctx.bc.append(Instr('YIELD_VALUE', lineno=node.lineno))


@py_expr_emit.case(ast.Return)
def py_expr_emit(node: ast.Return, ctx: Context):
    py_expr_emit(node.value)
    ctx.bc.append(Instr('RETURN_VALUE', lineno=node.lineno))


@py_expr_emit.case(ast.Pass)
def py_expr_emit(node: ast.Pass, ctx: Context):
    pass


@py_expr_emit.case(ast.UnaryOp)
def py_expr_emit(node: ast.UnaryOp, ctx: Context):
    py_expr_emit(node.value, ctx)
    inst = {
        ast.Not: "UNARY_NOT",
        ast.USub: "UNARY_NEGATIVE",
        ast.UAdd: "UNARY_POSITIVE",
        ast.Invert: "UNARY_INVERT"
    }.get(type(node.op))
    if inst:
        ctx.bc.append(Instr(inst, lineno=node.lineno))
    else:
        raise TypeError("type mismatched")


@py_expr_emit.case(ast.BinOp)
def py_expr_emit(node: ast.BinOp, ctx: Context):
    py_expr_emit(node.left, ctx)
    py_expr_emit(node.right, ctx)
    inst = {
        ast.Add: "BINARY_ADD",
        ast.BitAnd: "BINARY_AND",
        ast.Sub: "BINARY_SUBTRACT",
        ast.Div: "BINARY_TRUE_DIVIDE",
        ast.FloorDiv: "BINARY_FLOOR_DIVIDE",
        ast.LShift: "BINARY_LSHIFT",
        ast.RShift: "BINARY_RSHIFT",
        ast.MatMult: "BINARY_MATRIX_MULTIPLY",
        ast.Pow: "BINARY_POWER",
        ast.BitOr: "BINARY_OR",
        ast.BitXor: "BINARY_XOR",
        ast.Mult: "BINARY_MULTIPLY",
        ast.Mod: "BINARY_MODULO"
    }.get(type(node.op))
    if inst:
        ctx.bc.append(Instr(inst, lineno=node.lineno))
    else:
        raise TypeError("type mismatched")


@py_expr_emit.case(ast.BoolOp)
def py_expr_emit(node: ast.BoolOp, ctx: Context):
    inst = {
        ast.And: "JUMP_IF_FALSE_OR_POP",
        ast.Or: "JUMP_IF_TRUE_OR_POP"
    }.get(type(node.op))
    if inst:
        label = Label()
        for expr in node.values[:-1]:
            py_expr_emit(expr, ctx)
            ctx.bc.append(Instr(inst, label, lineno=node.lineno))
        py_expr_emit(node.values[-1], ctx)
        ctx.bc.append(label)
    else:
        raise TypeError("type mismatched")


@py_expr_emit.case(ast.Num)
def py_expr_emit(node: ast.Num, ctx: Context):
    ctx.bc.append(Instr("LOAD_CONST", node.n, lineno=node.lineno))
