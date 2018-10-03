import ast
from yapypy.extended_python.pybc_emit import py_compile
from yapypy.extended_python.parser import parse
from Redy.Tools.PathLib import Path
from os.path import splitext
from textwrap import dedent
from bytecode import Bytecode
import rbnf.zero as ze
import unittest
ze_exp = ze.compile(
    r"""
[python] import rbnf.std.common.[recover_codes]
Space   := ' '
NL      := R'\n'
Keyword := 'test:' 'prepare:' '>>>'
Doctest ::= [(~'prepare:')* 'prapare:' ((~'>>>')* '>>>' prepare_lines<< (~NL)+)*]
            (~'test:')* 'test:' ((~'>>>')* '>>>' test_lines<< (~NL)+)* 
            -> (tuple(map(recover_codes, prepare_lines)) if prepare_lines else (), 
                tuple(map(recover_codes, test_lines)))
lexer   := R'.'
""",
    use='Doctest')

yapypy = Path('yapypy')


def dedent_all(text: str):
    while text.startswith(' ') or text.startswith('\t'):
        text = dedent(text)
    return text


class DocStringsCollector(ast.NodeVisitor):
    def __init__(self):
        self.docs = {}

    def _visit_fn(self, node: ast.FunctionDef):
        head, *_ = node.body
        if isinstance(head, ast.Expr):
            value = head.value
            if isinstance(value, ast.Str):
                self.docs[node.name] = node.lineno, *ze_exp.match(
                    value.s).result
        self.generic_visit(node)


for each in filter(lambda p: p[-1].endswith('.py'), yapypy.collect()):
    if each.parent().exists():
        pass
    else:
        each.parent().mkdir()

    with each.open('r') as fr:
        collector = DocStringsCollector()
        mod = ast.parse(fr.read())
        collector.visit(mod)

    suites = []

    filename = each.__str__()
    mod_name, _ = splitext(each.relative())
    for idx, (fn_name, (lineno, prepare_suites,
                        test_suites)) in enumerate(collector.docs.items()):

        context = {}
        try:
            code = compile(
                dedent_all('\n'.join(prepare_suites)), filename, "exec")
        except SyntaxError as exc:
            exc.lineno = lineno
            exc.filename = filename
            raise exc
        bc = Bytecode.from_code(code)
        bc.filename = filename
        bc.first_lineno = lineno
        exec(bc.to_code(), context)
        try:
            code = py_compile(
                parse(dedent_all('\n'.join(prepare_suites))).result)
        except SyntaxError as exc:
            exc.lineno = lineno
            exc.filename = filename
            raise exc
        bc = Bytecode.from_code(code)
        bc.filename = filename
        bc.first_lineno = lineno
        exec(bc.to_code(), context)
