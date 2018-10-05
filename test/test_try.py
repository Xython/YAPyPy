# -*- coding: utf-8 -*-

import ast
from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.py_compile import py_compile

code = r"""
try:
    a = b
except NameError as e:
    a = 3
    print( a )
except ValueError as e:
    a = 4
    print( a )
else:
    a = 5
    print( a )
finally:
    a = -1
    print( a )
"""
res: Tag = to_tagged_ast(parse(code).result)
co = py_compile(res)
import dis
dis.dis(co)
print( dis.code_info(co) )
from bytecode import Bytecode
for i in Bytecode.from_code(co):
    print(i)
exec(co)