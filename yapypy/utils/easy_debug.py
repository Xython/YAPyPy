import ast
import dis
from typing import AnyStr

import astpretty
from os import path, pardir
from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile
from yapypy.extended_python.symbol_analyzer import to_tagged_ast

LOCAL_DIR = path.dirname(path.abspath(__file__))
TEST_DIR = path.join(path.join(path.join(LOCAL_DIR, pardir), pardir), 'test')


def _read_test_file(file_name: str) -> AnyStr:
    test_file = path.join(TEST_DIR, f'{file_name}.py_test')
    with open(test_file) as f:
        test_code = f.read()
        return test_code


def _read_abs_test_file(file_path: str) -> AnyStr:
    with open(file_path) as f:
        test_code = f.read()
        return test_code


def yapypy_test_abs(file_path: str, should_exec=False, ctx=None):
    code = _read_abs_test_file(file_path)
    if code is None:
        return

    yapypy_test_code(code, should_exec, ctx)
    return True


def yapypy_test(file_name: str, should_exec=False, ctx=None):
    code = _read_test_file(file_name)
    if code is None:
        return

    yapypy_test_code(code, should_exec, ctx)
    return True


def yapypy_test_code(code: str, should_exec=False, ctx=None):
    res = to_tagged_ast(parse(code).result)
    c = py_compile(res)
    if should_exec:
        exec(c, ctx or {})


def yapypy_debug(code: str, should_exec=False, ctx=None):
    res = to_tagged_ast(parse(code).result)
    c = py_compile(res)
    print("-----------Code")
    print(code)
    print("-----------YaPyPy")
    print(dis.dis(c))
    print("-----------YaPyPy exec result")
    if should_exec:
        exec(c, ctx or {})
    else:
        print("\t(skip)")


def easy_debug(code: str, should_exec=False, ctx=None):
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
    exec(code, ctx or {})
    print("-----------YaPyPy exec result")
    if should_exec:
        exec(c, ctx or {})
    else:
        print("\t(skip)")
