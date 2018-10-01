import ast
from typing import NamedTuple
from kizmi.extended_python.symbol_analyzer import SymTable, Tag
from kizmi.utils.namedlist import INamedList, as_namedlist, trait
from kizmi.utils.instrs import *
from Redy.Magic.Pattern import Pattern
from bytecode import *
from bytecode.concrete import FreeVar, CellVar
from bytecode.flags import CompilerFlags


class IndexedAnalyzedSymTable(NamedTuple):
    bounds: list
    freevars: list
    cellvars: list
    borrowed_cellvars: list

    @classmethod
    def from_raw(cls, tb):
        return cls(*[list(each) for each in tb.analyzed])


class Context(INamedList, metaclass=trait(as_namedlist)):
    bc: Bytecode
    sym_tb: IndexedAnalyzedSymTable
    parent: 'Context'

    def update(self, bc=None, sym_tb=None, parent=None):
        return Context(bc if bc is not None else self.bc,
                       sym_tb if sym_tb is not None else self.sym_tb,
                       parent if parent is not None else self.parent)

    def enter_new(self, tag_table: SymTable):
        sym_tb = IndexedAnalyzedSymTable.from_raw(tag_table)
        bc = Bytecode()
        if tag_table.depth > 1:
            bc.flags |= CompilerFlags.NESTED

        if not sym_tb.freevars:
            bc.flags |= CompilerFlags.NOFREE
        else:
            bc.freevars.extend(sym_tb.freevars)

        bc.cellvars.extend(sym_tb.cellvars)
        return self.update(parent=self, bc=Bytecode(), sym_tb=sym_tb)

    def load_name(self, name, lineno=None):
        sym_tb = self.sym_tb
        if name in sym_tb.cellvars:
            self.bc.append(Instr('LOAD_DEREF', CellVar(name), lineno=lineno))
        elif name in sym_tb.freevars:
            self.bc.append(Instr('LOAD_DEREF', FreeVar(name), lineno=lineno))
        elif name in sym_tb.bounds:
            self.bc.append(Instr('LOAD_FAST', name, lineno=lineno))
        self.bc.append(Instr("LOAD_GLOBAL", name, lineno=lineno))

    def store_name(self, name, lineno=None):
        sym_tb = self.sym_tb
        if name in sym_tb.cellvars:
            self.bc.append(Instr('STORE_DEREF', CellVar(name), lineno=lineno))
        elif name in sym_tb.freevars:
            self.bc.append(Instr('STORE_DEREF', FreeVar(name), lineno=lineno))
        elif name in sym_tb.bounds:
            self.bc.append(Instr('STORE_FAST', name, lineno=lineno))
        self.bc.append(Instr("STORE_GLOBAL", name, lineno=lineno))

    def load_closure(self, lineno=None):
        parent = self.parent
        freevars = self.sym_tb.freevars
        if freevars:
            for each in self.sym_tb.freevars:
                if each in parent.sym_tb.cellvars:
                    parent.bc.append(
                        Instr('LOAD_CLOSURE', CellVar(each), lineno=lineno))
                elif each in parent.sym_tb.borrowed_cellvars:
                    parent.bc.append(
                        Instr('LOAD_CLOSURE', FreeVar(each), lineno=lineno))
                else:
                    raise RuntimeError
            parent.bc.append(Instr('BUILD_TUPLE', len(freevars)))


def py_compile(node: Tag):
    ctx = Context(Bytecode(), IndexedAnalyzedSymTable.from_raw(node.tag), None)
    py_emit(node.it, ctx)
    return ctx.bc.to_code()


@Pattern
def py_emit(node: ast.AST, ctx: Context):
    return type(node)


@py_emit.case(Tag)
def py_emit(node: Tag, ctx: Context):
    ctx = ctx.enter_new(node.tag)
    py_emit(node.it, ctx)


@py_emit.case(ast.Module)
def py_emit(node: ast.Module, ctx: Context):
    for each in node.body:
        py_emit(each, ctx)
    ctx.bc.append(Instr('LOAD_CONST', None))
    ctx.bc.append(Instr('RETURN_VALUE'))


@py_emit.case(ast.Str)
def py_emit(node: ast.Str, ctx: Context):
    ctx.bc.append(LOAD_CONST(node.s, lineno=node.s))


@py_emit.case(ast.JoinedStr)
def py_emit(node: ast.JoinedStr, ctx: Context):
    for each in node.values:
        py_emit(each, ctx)
    ctx.bc.append(BUILD_STRING(len(node.values), lineno=node.lineno))


@py_emit.case(ast.FormattedValue)
def py_emit(node: ast.FormattedValue, ctx: Context):
    raise NotImplemented


@py_emit.case(ast.Tuple)
def py_emit(node: ast.Tuple, ctx: Context):
    is_lhs = isinstance(node.ctx, ast.Store)
    if any(isinstance(each, ast.Starred) for each in node.elts):
        raise NotImplemented
    if is_lhs:
        UNPACK_SEQUENCE(len(node.elts), lineno=node.lineno)
        for each in node.elts:
            py_emit(each, ctx)
    else:
        for each in node.elts:
            py_emit(each, ctx)
        BUILD_TUPLE(len(node.elts), lineno=node.lineno)


@py_emit.case(ast.FunctionDef)
def py_emit(node: ast.FunctionDef, new_ctx: Context):
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
    for each in node.body:
        py_emit(each, new_ctx)

    args = node.args
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
    if arg and arg.annotation:
        argnames.append(arg.arg)
        annotations.append((arg.arg, arg.annotation))

    arg = args.kwarg
    if arg and arg.annotation:
        argnames.append(arg.arg)
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

    parent_ctx.bc.append(
        Instr('LOAD_CONST', new_ctx.bc.to_code(), lineno=node.lineno))

    ### when it comes to nested, the name is not generated correctly now.
    parent_ctx.bc.append(Instr('LOAD_CONST', node.name, lineno=node.lineno))

    parent_ctx.bc.append(
        Instr("MAKE_FUNCTION", make_function_flags, lineno=node.lineno))

    parent_ctx.store_name(node.name, lineno=node.lineno)


@py_emit.case(ast.Assign)
def py_emit(node: ast.Assign, ctx: Context):
    targets = node.targets
    value = node.value
    n = len(targets)
    py_emit(value, ctx)
    for _ in range(n - 1):
        ctx.bc.append(DUP_TOP(lineno=node.lineno))
    for each in targets:
        py_emit(each, ctx)


@py_emit.case(ast.Name)
def py_emit(node: ast.Name, ctx: Context):
    if isinstance(node.ctx, ast.Load):
        ctx.load_name(node.id, lineno=node.lineno)
    else:
        ctx.store_name(node.id, lineno=node.lineno)


@py_emit.case(ast.Expr)
def py_emit(node: ast.Expr, ctx: Context):
    py_emit(node.value, ctx)
    ctx.bc.append(Instr('POP_TOP', lineno=node.lineno))


@py_emit.case(ast.Call)
def py_emit(node: ast.Call, ctx: Context):
    py_emit(node.func, ctx)

    if not node.keywords:
        if not any(isinstance(each, ast.Starred) for each in node.args):
            for each in node.args:
                py_emit(each, ctx)
            ctx.bc.append(
                Instr('CALL_FUNCTION', len(node.args), lineno=node.lineno))
        else:
            raise NotImplemented
    else:
        raise NotImplemented


@py_emit.case(ast.YieldFrom)
def py_emit(node: ast.YieldFrom, ctx: Context):
    append = ctx.bc.append
    py_emit(node.value, ctx)
    append(Instr('GET_YIELD_FROM_ITER', lineno=node.lineno))
    append(Instr('LOAD_CONST', None, lineno=node.lineno))
    append(Instr("YIELD_FROM", lineno=node.lineno))


@py_emit.case(ast.Yield)
def py_emit(node: ast.Yield, ctx: Context):
    py_emit(node.value, ctx)
    ctx.bc.append(Instr('YIELD_VALUE', lineno=node.lineno))


@py_emit.case(ast.Return)
def py_emit(node: ast.Return, ctx: Context):
    py_emit(node.value, ctx)
    ctx.bc.append(Instr('RETURN_VALUE', lineno=node.lineno))


@py_emit.case(ast.Pass)
def py_emit(node: ast.Pass, ctx: Context):
    pass


@py_emit.case(ast.UnaryOp)
def py_emit(node: ast.UnaryOp, ctx: Context):
    py_emit(node.value, ctx)
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


@py_emit.case(ast.BinOp)
def py_emit(node: ast.BinOp, ctx: Context):
    py_emit(node.left, ctx)
    py_emit(node.right, ctx)
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


@py_emit.case(ast.BoolOp)
def py_emit(node: ast.BoolOp, ctx: Context):
    inst = {
        ast.And: "JUMP_IF_FALSE_OR_POP",
        ast.Or: "JUMP_IF_TRUE_OR_POP"
    }.get(type(node.op))
    if inst:
        label = Label()
        for expr in node.values[:-1]:
            py_emit(expr, ctx)
            ctx.bc.append(Instr(inst, label, lineno=node.lineno))
        py_emit(node.values[-1], ctx)
        ctx.bc.append(label)
    else:
        raise TypeError("type mismatched")


@py_emit.case(ast.Num)
def py_emit(node: ast.Num, ctx: Context):

    ctx.bc.append(Instr("LOAD_CONST", node.n, lineno=node.lineno))
