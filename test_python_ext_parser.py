from kizmi.extended_python.parser import parse
from kizmi.extended_python.symbol_analyzer import ASTTagger, SymTable


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

g = SymTable.global_context()

ASTTagger(g).visit(stmt)
g.analyze()
print(g.show_resolution())
