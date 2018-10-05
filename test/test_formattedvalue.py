# -*- coding: utf-8 -*-

from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile
from yapypy.extended_python.symbol_analyzer import to_tagged_ast, Tag


def test_formattedvalue():
    code = r"""


"""

    res: Tag = to_tagged_ast(parse(code).result)

    exec(py_compile(res))
