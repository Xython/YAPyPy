import ast
import dis
import sys
import typing
from typing import NamedTuple
from astpretty import pprint
import yapypy.extended_python.extended_ast as ex_ast
from yapypy.extended_python.symbol_analyzer import SymTable, Tag, to_tagged_ast, ContextType
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
    current_label_stack: list
    cts: typing.FrozenSet[ContextType]

    def enter_new(self, tag_table: SymTable):
        sym_tb = IndexedAnalyzedSymTable.from_raw(tag_table)
        bc = Bytecode()
        try:
            bc.filename = self.bc.filename
        except IndexError:
            bc.filename = ""

        cts = tag_table.cts

        if ContextType.Annotation in cts and (ContextType.ClassDef in cts
                                              or ContextType.Module in cts):
            bc.append(SETUP_ANNOTATIONS())

        if ContextType.Coroutine in cts:
            if ContextType.Generator in cts:
                bc.flags |= CompilerFlags.ASYNC_GENERATOR
            else:
                bc.flags |= CompilerFlags.COROUTINE
        elif ContextType.Generator in cts:
            bc.flags |= CompilerFlags.GENERATOR

        # not elif for further designing(async lambda)

        bc.flags |= CompilerFlags.NEWLOCALS
        if tag_table.depth > 1:
            bc.flags |= CompilerFlags.NESTED

        if not sym_tb.freevars:
            bc.flags |= CompilerFlags.NOFREE
        else:
            bc.freevars.extend(sym_tb.freevars)

        bc.cellvars.extend(sym_tb.cellvars)
        return Context(
            parent=self,
            bc=bc,
            sym_tb=sym_tb,
            current_label_stack=[],
            cts=frozenset(cts))

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

        if freevars is None:
            return

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

    def push_current_label(self, label: Label):
        self.current_label_stack.append(label)

    def pop_current_label(self):
        return self.current_label_stack.pop()

    def get_current_label(self):
        return self.current_label_stack[-1]


@Pattern
def py_emit(node: ast.AST, ctx: Context):
    return type(node)
