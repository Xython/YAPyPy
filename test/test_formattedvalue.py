# -*- coding: utf-8 -*-

import ast
from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.pybc_emit import py_compile
code = r"""
p = print
A = "A"

p (f'{A}')
p (f'{A!r}')
p (f'{A!s}')
p (f'{A!a}')

p (f'{A!r:>30}')
p (f'{A!r:<30}')

p (f'{A!r:^30}')
p (f'{A!r:*^20}')

p (f'{3.14:+f}')
p (f'{3.14:f}')
p (f'{3.14:-f}')
a = 233
p (f'{a:d} {a:x} {a:o} {a:b}')
p (f'{a:d} {a:#x} {a:#o} {a:#b}')

p (f'{123456789:,}')
p (f'{19/22:.2%}')
"p ( f'{time:%Y-%m-%d %H:%M:%S}' ) need import datetime"

"""

res: Tag = to_tagged_ast(parse(code).result)

exec(py_compile(res))
