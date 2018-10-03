import ast
from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.pybc_emit import py_compile


def test_call():
    code = r"""
a = 'a',
b = 'b',
c = 'c',
d = {'d': 0}
e = {'e': 1}
g = {'g': 2}
x = {'x': 3}
y = {'y': 4}


def f(*args, **kwargs):
    print(args, kwargs)

f(1, c=3, d=4)

f(1, 2, *a, 3, *b, *c, 4, **e, **g)
f(1, *b, d=4)

f(1, 2, 3, a=1, b=2)
f(*a, 1, *a, 2, 3, *b, *e, 3, *c, **x, **y)
f(*a, 1, *a, 2, *b, 3, *c, **x, **y)
f(1, *a, 2, *b, 3, *c, **x, **y)
f(1, 2, **e, **d)
f(**e, **d)
f(*b, **d)
f(*b)
f(a, *b)
f(1, 2, *c, **d, **e)
f(1, 2, *c)
f(1, 2, y=1, *x, a=1, b=2, c=3, **d)
f(1, 2, y=1, *x, a=1, b=2, c=3, **d, e=4)
    """

    res: Tag = to_tagged_ast(parse(code).result)

    exec(py_compile(res))
