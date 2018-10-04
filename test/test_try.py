# -*- coding: utf-8 -*-

import ast
from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.py_compile import py_compile

code = r"""
try:
    raise
except TypeError as e:
    a = 3
except NameError as e:
    a = 4
except RuntimeError as e:
    a = 5
"""
res: Tag = to_tagged_ast(parse(code).result)
co = py_compile(res)
import dis
dis.dis(co)
print( dis.code_info(co) )
exec(co)
print( a )