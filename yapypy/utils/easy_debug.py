import ast
import dis

import astpretty

from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile
from yapypy.extended_python.symbol_analyzer import to_tagged_ast


def easy_debug(code: str, should_exec=False):
    res = to_tagged_ast(parse(code).result)
    c = py_compile(res)
    print("-----------code")
    print(code)
    print("-----------Python")
    print(dis.dis(code))
    print("-----------YaPyPy")
    print(dis.dis(c))
    print("-----------astpretty")
    astpretty.pprint(ast.parse(code))
    print("----------- Python exec result")
    exec(code)
    print("-----------YaPyPy exec result")
    if should_exec:
        exec(c)
    else:
        print("\t(skip)")
