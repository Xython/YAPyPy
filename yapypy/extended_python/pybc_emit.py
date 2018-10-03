import ast
from typing import NamedTuple
import yapypy.extended_python.extended_ast as ex_ast
from yapypy.extended_python.symbol_analyzer import SymTable, Tag
from yapypy.utils.namedlist import INamedList, as_namedlist, trait
from yapypy.utils.instrs import *
from Redy.Magic.Pattern import Pattern
from bytecode import *
from bytecode.concrete import FreeVar, CellVar, Compare
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
        bc.flags |= CompilerFlags.NEWLOCALS
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
        else:
            self.bc.append(Instr("LOAD_GLOBAL", name, lineno=lineno))

    def del_name(self, name, lineno=None):
        sym_tb = self.sym_tb
        if name in sym_tb.cellvars:
            self.bc.append(Instr('DELETE_DEREF', CellVar(name), lineno=lineno))
        elif name in sym_tb.freevars:
            self.bc.append(Instr('DELETE_DEREF', FreeVar(name), lineno=lineno))
        elif name in sym_tb.bounds:
            self.bc.append(Instr('DELETE_FAST', name, lineno=lineno))
        else:
            self.bc.append(Instr("DELETE_GLOBAL", name, lineno=lineno))

    def store_name(self, name, lineno=None):
        sym_tb = self.sym_tb
        if name in sym_tb.cellvars:
            self.bc.append(Instr('STORE_DEREF', CellVar(name), lineno=lineno))
        elif name in sym_tb.freevars:
            self.bc.append(Instr('STORE_DEREF', FreeVar(name), lineno=lineno))
        elif name in sym_tb.bounds:
            self.bc.append(Instr('STORE_FAST', name, lineno=lineno))
        else:
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
    ctx.bc.append(LOAD_CONST(node.s, lineno=node.lineno))


@py_emit.case(ast.JoinedStr)
def py_emit(node: ast.JoinedStr, ctx: Context):
    for each in node.values:
        py_emit(each, ctx)
    ctx.bc.append(BUILD_STRING(len(node.values), lineno=node.lineno))


@py_emit.case(ast.FormattedValue)
def py_emit(node: ast.FormattedValue, ctx: Context):
    conversion = node.conversion
    format_spec = node.format_spec
    value = node.value
    maps = {
        97: 3,  # ascii
        114: 2,  # repr
        115: 1,  # str
        -1: 0,  # None
    }
    py_emit(value, ctx)
    flags = maps[conversion]
    if format_spec:
        py_emit(format_spec, ctx)
        flags += 4
    ctx.bc.append(Instr("FORMAT_VALUE", flags))


@py_emit.case(ast.Raise)
def py_emit(node: ast.Raise, ctx: Context):
    """
    test:
    >>> try:
    ...     raise
    ... except RuntimeError as e:
    ...     assert isinstance(e,RuntimeError)
    >>> try:
    ...     raise TypeError('typeerror')
    ... except TypeError as e:
    ...     assert isinstance(e,TypeError)
    >>> try:
    ...     raise ValueError('value') from NameError('name')
    ... except ValueError as e:
    ...     assert isinstance(e,ValueError)
    ...     assert isinstance(e.__cause__,NameError)
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
    ctx.bc.append(Instr("RAISE_VARARGS", argc))


@py_emit.case(ast.Assert)
def py_emit(node: ast.Assert, ctx: Context):
    """
    test:
    >>> try:
    ...     assert 0,"num is zero"
    ... except AssertError as e:
    ...     assert isinstance(e,AssertError)
    """
    test = node.test
    msg = node.msg
    label = Label()
    py_emit(test, ctx)
    ctx.bc.append(Instr("POP_JUMP_IF_TRUE", label))
    # current_pos = ctx.bc.__len__() - 1
    # calc msg and
    ctx.bc.append(Instr("LOAD_GLOBAL", "AssertionError"))
    if msg:
        py_emit(msg, ctx)
        ctx.bc.append(Instr("CALL_FUNCTION", 1)) # AssertError(<arg>) , awalys 1
    ctx.bc.append(Instr("RAISE_VARARGS", 1)) # <argc> awalys 1
    ctx.bc.append(label)
    #ctx.bc[current_pos] = ctx.bc.__len__()


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
    print(new_ctx.bc)
    inner_code = new_ctx.bc.to_code()

    parent_ctx.bc.append(Instr('LOAD_CONST', inner_code, lineno=node.lineno))

    ### when it comes to nested, the name is not generated correctly now.
    parent_ctx.bc.append(Instr('LOAD_CONST', node.name, lineno=node.lineno))

    parent_ctx.bc.append(
        Instr("MAKE_FUNCTION", make_function_flags, lineno=node.lineno))

    parent_ctx.store_name(node.name, lineno=node.lineno)


@py_emit.case(ex_ast.ExDict)
def py_emit(node: ast.Dict, ctx: Context):
    keys = node.keys
    values = node.values
    if any(each for each in keys if each is None):
        raise NotImplemented
    for key, value in zip(keys, values):
        py_emit(key, ctx)
        py_emit(value, ctx)
    ctx.bc.append(Instr('BUILD_MAP', len(keys), lineno=node.lineno))


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
    {
        ast.Load: ctx.load_name,
        ast.Store: ctx.store_name,
        ast.Del: ctx.del_name
    }[type(node.ctx)](
        node.id, lineno=node.lineno)


@py_emit.case(ast.Expr)
def py_emit(node: ast.Expr, ctx: Context):
    py_emit(node.value, ctx)
    ctx.bc.append(POP_TOP(lineno=node.lineno))


@py_emit.case(ast.Call)
def py_emit(node: ast.Call, ctx: Context):
    py_emit(node.func, ctx)

    has_star = False
    has_key = False
    has_star_star = False

    for each in node.args:
        if isinstance(each, ast.Starred):
            has_star = True
            break
    for each in node.keywords:
        if each.arg:
            has_key = True
            break
    for each in node.keywords:
        if each.arg is None:
            has_star_star = True
            break

    # positional arguments
    if has_star or has_star_star:
        arg_count = 0
        arg_tuple_count = 0
        for each in node.args:
            if not isinstance(each, ast.Starred):
                py_emit(each, ctx)
                arg_count += 1
            else:
                if arg_count:
                    ctx.bc.append(
                        Instr("BUILD_TUPLE", arg_count, lineno=node.lineno))
                    arg_tuple_count += 1
                    arg_count = 0
                py_emit(each.value, ctx)
                arg_tuple_count += 1

        if arg_count:
            ctx.bc.append(Instr("BUILD_TUPLE", arg_count, lineno=node.lineno))
            arg_tuple_count += 1

        if arg_tuple_count > 1:
            ctx.bc.append(
                Instr(
                    "BUILD_TUPLE_UNPACK_WITH_CALL",
                    arg_tuple_count,
                    lineno=node.lineno))
        elif arg_tuple_count == 1:
            pass
        elif arg_tuple_count == 0:
            ctx.bc.append(Instr("BUILD_TUPLE", 0, lineno=node.lineno))
    else:
        for each in node.args:
            py_emit(each, ctx)

    # keyword arguments
    if has_star or has_star_star:
        karg_pack_count = 0
        keys = []
        values = []
        karg_count = 0
        # use dummy node handle trailing keyword arguments
        dummy_node = ast.keyword(arg=None)
        node.keywords.append(dummy_node)
        for each in node.keywords:
            if each.arg:
                keys.append(each.arg)
                values.append(each.value)
                karg_count += 1
            else:
                if karg_count:
                    karg_pack_count += 1
                    if karg_count > 1:
                        for value in values:
                            py_emit(value, ctx)
                        ctx.bc.append(
                            Instr(
                                "LOAD_CONST", tuple(keys), lineno=node.lineno))
                        ctx.bc.append(
                            Instr(
                                "BUILD_CONST_KEY_MAP",
                                karg_count,
                                lineno=node.lineno))
                    elif karg_count == 1:
                        ctx.bc.append(
                            Instr("LOAD_CONST", keys[0], lineno=node.lineno))
                        py_emit(values[0], ctx)
                        ctx.bc.append(
                            Instr("BUILD_MAP", 1, lineno=node.lineno))
                    keys = []
                    values = []
                    karg_count = 0
                if each is dummy_node:
                    break
                py_emit(each.value, ctx)
                karg_pack_count += 1
        node.keywords.pop(-1)  # pop dummy node
        if karg_pack_count > 1:
            ctx.bc.append(
                Instr(
                    "BUILD_MAP_UNPACK_WITH_CALL",
                    karg_pack_count,
                    lineno=node.lineno))
    else:
        keys = []
        for each in node.keywords:
            py_emit(each.value, ctx)
            keys.append(each.arg)
        if keys:
            ctx.bc.append(Instr("LOAD_CONST", tuple(keys), lineno=node.lineno))

    if has_star or has_star_star:
        ctx.bc.append(
            Instr(
                "CALL_FUNCTION_EX",
                has_star_star | has_key,
                lineno=node.lineno))
    elif has_key:
        ctx.bc.append(
            Instr(
                "CALL_FUNCTION_KW",
                len(node.args) + len(node.keywords),
                lineno=node.lineno))
    else:
        ctx.bc.append(
            Instr('CALL_FUNCTION', len(node.args), lineno=node.lineno))


@py_emit.case(ast.YieldFrom)
def py_emit(node: ast.YieldFrom, ctx: Context):
    append = ctx.bc.append
    py_emit(node.value, ctx)
    append(Instr('GET_YIELD_FROM_ITER', lineno=node.lineno))
    append(Instr('LOAD_CONST', None, lineno=node.lineno))
    append(Instr("YIELD_FROM", lineno=node.lineno))


@py_emit.case(ast.Attribute)
def py_emit(node: ast.Attribute, ctx: Context):
    py_emit(node.value, ctx)

    ctx.bc.append({
        ast.Store: STORE_ATTR,
        ast.Load: LOAD_ATTR,
        ast.Del: DELETE_ATTR
    }[type(node.ctx)](node.attr, lineno=node.lineno))


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


@py_emit.case(ast.Nonlocal)
def py_emit(_1, _2):
    pass


@py_emit.case(ast.Global)
def py_emit(_1, _2):
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
        raise TypeError


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
        raise TypeError


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
        raise TypeError


@py_emit.case(ast.Num)
def py_emit(node: ast.Num, ctx: Context):

    ctx.bc.append(Instr("LOAD_CONST", node.n, lineno=node.lineno))


@py_emit.case(ast.Import)
def py_emit(node: ast.Import, ctx: Context):
    for name in node.names:
        ctx.bc.append(
            Instr("LOAD_CONST", 0,
                  lineno=node.lineno))  # TOS1 for level, default to zero
        ctx.bc.append(Instr("LOAD_CONST", None,
                            lineno=node.lineno))  # TOS for fromlist()
        ctx.bc.append(Instr("IMPORT_NAME", name.name, lineno=node.lineno))
        as_name = name.name or name.asname
        ctx.store_name(as_name, lineno=node.lineno)


@py_emit.case(ast.ImportFrom)
def py_emit(node: ast.ImportFrom, ctx: Context):
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
            as_name = name.name or name.asname
            ctx.store_name(as_name, lineno=lineno)
        ctx.bc.append(POP_TOP(lineno=lineno))

@py_emit.case(ast.ListComp)
def py_emit(node: ast.ListComp, ctx: Context):
    loop_start = Label()
    loop_done = Label()
    loop_exit = Label()

    append = ctx.bc.append
    append(Instr("BUILD_LIST", lineno=node.lineno))
    append(Instr("LOAD_FAST", '.0', lineno=node.lineno))
    append(loop_start)
    append(Instr("FOR_ITER", loop_done))
    py_emit(node.generators[0].target)
    py_emit(node.generators[0].iter)
    py_emit(node.elt)
    append(Instr("LIST_APPEND"))
    append(Instr("JUMP_ABSOLUTE", loop_start))
    append(loop_exit)



@py_emit.case(ast.Compare)
def py_emit(node: ast.Compare, ctx: Context):
    """
    test:
    >>> 1 == 1
    >>> 1 != 1
    >>> 1 > 1
    >>> 1 >= 2
    >>> 1 < 1
    >>> 1 <= 2
    >>> 1 is 1
    >>> 1 is not 1
    >>> 1 in range(2)
    >>> 1 not in range(3)
    >>> 1 == 1 != 2 > 1 >= 1 < 2 <= 2 is 2 is not 3 in range(3) not in range(3)
    """
    ops = {
        ast.Eq: Compare.EQ,
        ast.NotEq: Compare.NE,
        ast.Lt: Compare.LT,
        ast.LtE: Compare.LE,
        ast.Gt: Compare.GT,
        ast.GtE: Compare.GE,
        ast.Is: Compare.IS,
        ast.IsNot: Compare.IS_NOT,
        ast.In: Compare.IN,
        ast.NotIn: Compare.NOT_IN,
    }
    len_of_comparators = len(node.comparators)
    is_multiple = len_of_comparators > 1

    py_emit(node.left, ctx)
    if is_multiple:
        last_idx_of_comparators = len_of_comparators - 1
        label_rot = Label()
        label_out = Label()

        for idx in range(len_of_comparators):
            op_type = type(node.ops[idx])
            op = ops.get(op_type)
            expr = node.comparators[idx]

            py_emit(expr, ctx)
            if idx == last_idx_of_comparators:
                ctx.bc.append(Instr("JUMP_FORWARD", label_out))
            else:
                ctx.bc.append(Instr("DUP_TOP"))
                ctx.bc.append(Instr("ROT_THREE"))
                ctx.bc.append(Instr("COMPARE_OP", op, lineno=node.lineno))
                ctx.bc.append(Instr("JUMP_IF_FALSE_OR_POP", label_rot))

        ctx.bc.append(label_rot)
        ctx.bc.append(Instr("ROT_TWO"))
        ctx.bc.append(Instr("POP_TOP"))
        ctx.bc.append(label_out)
    else:
        py_emit(node.comparators[0], ctx)
        op_type= type(node.ops[0])
        op = ops.get(op_type)
        ctx.bc.append(Instr("COMPARE_OP", op, lineno=node.lineno))
