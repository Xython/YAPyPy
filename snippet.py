"""
Update note: Never use this module to test your emit functions.
Use the file `auto_test.py` in the same directory instead.

"""

import ast
from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.pybc_emit import py_compile
import dis


def parse_expr(expr_code):
    return parse(expr_code).result.body[0].value


stmt = parse("""
print(1)
def f(x):
    a = 1
    def g(y):
        a + 1
        def u(z):
            k = 1
            v + k
    v = 3
    k = 4
""").result

res: Tag = to_tagged_ast(stmt)
print(res.tag.show_resolution())

stmt = parse("""
assert not hasattr(1, 'x')
""").result

pprint(stmt)
exec(py_compile(stmt))

try:
    parse_expr('f(a=1, b)\n')
except SyntaxError:
    print('good')
