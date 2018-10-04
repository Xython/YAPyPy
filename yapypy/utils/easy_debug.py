import ast
import dis

import astpretty

from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile
from yapypy.extended_python.symbol_analyzer import to_tagged_ast


def easy_debug(code: str, should_exec=False):
    res = to_tagged_ast(parse(code).result)
    c = py_compile(res)
    print("-----------Python")
    print(dis.dis(code))
    print("-----------YaPyPy")
    print(dis.dis(c))
    print("-----------astpretty")
    astpretty.pprint(ast.parse(code))
    if should_exec:
        print("-----------exec result")
        exec(c)
