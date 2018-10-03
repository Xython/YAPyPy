# -*- coding: utf-8 -*-

import ast
from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.pybc_emit import py_compile


def test_formattedvalue():
    code = r"""


"""

    res: Tag = to_tagged_ast(parse(code).result)

    exec(py_compile(res))
