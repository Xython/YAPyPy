import ast
from kizmi.utils.namedlist import INamedList, as_namedlist, trait
from typing import NamedTuple, List, Optional


class AnalyzedSymTable(NamedTuple):
    bounds: Optional[set]
    freevars: Optional[set]
    cellvars: Optional[set]


class SymTable(INamedList, metaclass=trait(as_namedlist)):
    requires: set
    entered: set
    explicit_nonlocals: set
    explicit_globals: set
    parent: Optional['SymTable']
    children: List['SymTable']
    depth: int  # to test if it is global context
    analyzed: Optional[AnalyzedSymTable]

    def update(self,
               requires: set = None,
               entered: set = None,
               explicit_nonlocals=None,
               explicit_globals=None,
               parent=None,
               children=None,
               depth=None,
               analyzed=None):
        return SymTable(
            requires if requires is not None else self.requires,
            entered if entered is not None else self.entered,
            explicit_nonlocals if explicit_nonlocals is not None else
            self.explicit_nonlocals, explicit_globals
            if explicit_globals is not None else self.explicit_globals,
            parent if parent is not None else self.parent,
            children if children is not None else self.children,
            depth if depth is not None else self.depth,
            analyzed if analyzed is not None else self.analyzed)

    @staticmethod
    def global_context():
        return SymTable(set(), set(), set(), set(), None, [], 0, None)

    def enter_new(self):
        new = self.update(
            requires=set(),
            entered=set(),
            explicit_globals=set(),
            explicit_nonlocals=set(),
            parent=self,
            children=[],
            depth=self.depth + 1)
        self.children.append(new)
        return new

    def can_resolve_by_parents(self, symbol: str):
        parent = self.parent

        return parent and (symbol in parent.analyzed.bounds or parent.parent
                           and parent.parent.can_resolve_by_parents(symbol))

    def resolve_bounds(self):
        enters = self.entered
        nonlocals = self.explicit_nonlocals
        globals_ = self.explicit_globals
        bounds = {
            each
            for each in enters
            if each not in nonlocals and each not in globals_
        }
        self.analyzed = AnalyzedSymTable(bounds, set(), set())
        return bounds

    def resolve_freevars(self):
        enters = self.entered
        requires = self.requires - enters
        nonlocals = self.explicit_nonlocals
        self.analyzed.freevars.update(
            nonlocals.union({
                each
                for each in requires if self.can_resolve_by_parents(each)
            }))

    def resolve_cellvars(self):
        analyzed = self.analyzed
        analyzed.cellvars.update(
            set.union(set(),
                      *(each.analyze().freevars
                        for each in self.children)).intersection(
                            analyzed.bounds))

    def analyze(self):
        if self.analyzed:
            return self.analyzed
        if self.depth is 0:
            # global context
            analyzed = self.analyzed = AnalyzedSymTable(set(), set(), set())
            for each in self.children:
                each.analyze()
            return analyzed
        else:
            self.resolve_bounds()
            self.resolve_freevars()
            self.resolve_cellvars()
            return self.analyzed


class Tag(NamedTuple):
    it: ast.AST
    tag: SymTable


class ASTTagger(ast.NodeTransformer):
    def __init__(self, symtable: SymTable):
        self.symtable = symtable

    def visit_Name(self, node: ast.Name):
        symtable = self.symtable
        name = node.id
        if isinstance(node.ctx, ast.Store):
            symtable.entered.add(name)
        elif isinstance(node.ctx, ast.Load):
            symtable.requires.add(name)


if __name__ == '__main__':
    g = SymTable.global_context()

    new = g.enter_new()
    new.entered.update('a')
    nested = new.enter_new()
    nested.requires.update('a')
    g.analyze()
    print(g.analyzed)
    print(new.analyzed)
    print(nested.analyzed)
