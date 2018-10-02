import ast
from astpretty import pprint
from kizmi.extended_python.parser import parse
from kizmi.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from kizmi.extended_python.pybc_emit import py_compile
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
def f(x):
    x

print(f(1))
x, y = 1, 2
print(x, y)
""").result

res: Tag = to_tagged_ast(stmt)

code = py_compile(res)

dis.dis(code)

exec(code)

try:
    parse_expr('f(a=1, b)\n')
except SyntaxError:
    print('good')
