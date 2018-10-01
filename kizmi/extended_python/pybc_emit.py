import ast
from typing import NamedTuple
from kizmi.extended_python.symbol_analyzer import SymTable, Tag, Suite
from kizmi.utils.namedlist import INamedList, as_namedlist, trait
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


    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method)
        return visitor(node)

    def visit_Tag(self, node):
        ctx.enter_new(node.tag).visit(node.it)

    def visit_Module(self, node):
        for each in node.body:
            self.visit(each)
        self.bc.append(Instr('LOAD_CONST', None))
        self.bc.append(Instr('RETURN_VALUE'))

    def visit_Suite(self, node):
        for each in node.stmts:
            ctx.visit(each)

    def visit_FunctionDef(self, node):
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
        parent_ctx: Context = self.parent
        for each in node.body:
            self.visit(each)

        args = node.args
        make_function_flags = 0
        if self.sym_tb.freevars:
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
        self.bc.argnames.extend(argnames)

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
            self.load_closure(lineno=node.lineno)

        self.bc.append(Instr('LOAD_CONST', None))
        self.bc.append(Instr('RETURN_VALUE'))

        parent_ctx.bc.append(
            Instr('LOAD_CONST', self.bc.to_code(), lineno=node.lineno))

        ### when it comes to nested, the name is not generated correctly now.
        parent_ctx.bc.append(Instr('LOAD_CONST', node.name, lineno=node.lineno))

        parent_ctx.bc.append(
            Instr("MAKE_FUNCTION", make_function_flags, lineno=node.lineno))

        parent_ctx.store_name(node.name, lineno=node.lineno)


    def visit_Assign(self, node):
        raise NotImplementedError

    def visit_Name(self, node):
        self.load_name(node.id, lineno=node.lineno)

    def visit_Expr(self, node):
        self.visit(node.value)
        self.bc.append(Instr('POP_TOP', lineno=node.lineno))

    def visit_Call(self, node):
        self.visit(node.func)

        if not node.keywords:
            if not any(isinstance(each, ast.Starred) for each in node.args):
                for each in node.args:
                    self.visit(each)
                self.bc.append(
                    Instr('CALL_FUNCTION', len(node.args), lineno=node.lineno))
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def visit_YieldFrom(self, node):
        append = self.bc.append
        self.visit(node.value)
        self.bc.append(Instr('GET_YIELD_FROM_ITER', lineno=node.lineno))
        self.bc.append(Instr('LOAD_CONST', None, lineno=node.lineno))
        self.bc.append(Instr("YIELD_FROM", lineno=node.lineno))

    def visit_Yield(self, node):
        self.visit(node.value)
        self.bc.append(Instr('YIELD_VALUE', lineno=node.lineno))

    def visit_Return(self, node):
        self.visit(node.value)
        self.bc.append(Instr('RETURN_VALUE', lineno=node.lineno))

    def visit_Pass(self, node):
        pass

    def visit_UnaryOp(self, node):
        self.visit(node.value)
        inst = {
            ast.Not: "UNARY_NOT",
            ast.USub: "UNARY_NEGATIVE",
            ast.UAdd: "UNARY_POSITIVE",
            ast.Invert: "UNARY_INVERT"
        }.get(type(node.op))
        if inst:
            self.bc.append(Instr(inst, lineno=node.lineno))
        else:
            raise TypeError("type mismatched")

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
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
            self.bc.append(Instr(inst, lineno=node.lineno))
        else:
            raise TypeError("type mismatched")

    def visit_BoolOp(self, node):
        inst = {
            ast.And: "JUMP_IF_FALSE_OR_POP",
            ast.Or: "JUMP_IF_TRUE_OR_POP"
        }.get(type(node.op))
        if inst:
            label = Label()
            for expr in node.values[:-1]:
                self.visit(expr)
                self.bc.append(Instr(inst, label, lineno=node.lineno))
            self.visit(node.values[-1])
            self.bc.append(label)
        else:
            raise TypeError("type mismatched")

    def visit_Num(node):
        self.bc.append(Instr("LOAD_CONST", node.n, lineno=node.lineno))


def py_compile(node: Tag):
    ctx = Context(Bytecode(), IndexedAnalyzedSymTable.from_raw(node.tag), None)
    ctx.visit(node.it)
    return ctx.bc.to_code()
