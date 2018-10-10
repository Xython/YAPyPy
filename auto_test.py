import ast
import unittest
from os.path import splitext
from textwrap import dedent

import pytest
import rbnf.zero as ze
from Redy.Tools.PathLib import Path
from bytecode import Bytecode

from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile

ze_exp = ze.compile(
    r"""
[python] import rbnf.std.common.[recover_codes]
Space   := ' '
NL      := R'\n'
Keyword := 'test:' 'prepare:' '>>>' 'title:' 
NoSwitch ::= ~Keyword
Doctest ::= [(~'title:')* 'title:' name=(~NL)+]
            [(~'prepare:')* 'prepare:' (NoSwitch* '>>>' prepare_lines<<((~NL)+) NL+)*]
            (~'test:')* 'test:' (NoSwitch* '>>>' test_lines<<((~NL)+))* 
            ->
              prepare_lines = recover_codes(sum(prepare_lines, [])) if prepare_lines else ''
              test          = recover_codes(sum(test_lines, []))    if test_lines else ''
              return recover_codes(name) if name else None, prepare_lines, test
                
lexer   := R'.'
TestCase ::= [it=Doctest] _* -> it or None
""",
    use='TestCase')

yapypy = Path('yapypy')


def dedent_all(text: str):
    while text.startswith(' ') or text.startswith('\t'):
        text = dedent(text)
    return text


class DocStringsCollector(ast.NodeVisitor):
    def __init__(self):
        self.docs = []

    def _visit_fn(self, node: ast.FunctionDef):
        head, *_ = node.body

        if isinstance(head, ast.Expr):
            value = head.value
            if isinstance(value, ast.Str):
                res = ze_exp.match(value.s).result

                if res:
                    self.docs.append((node.name, node.lineno, *res))
        self.generic_visit(node)

    visit_FunctionDef = _visit_fn


class FixLineno(ast.NodeVisitor):
    def __init__(self, first_lineno: int):
        self.first_lineno = first_lineno

    def visit(self, node):
        if hasattr(node, 'lineno'):
            node.lineno += self.first_lineno
        self.generic_visit(node)


class Test(unittest.TestCase):
    def test_all(self):
        for each in filter(lambda p: p[-1].endswith('.py'), yapypy.collect()):
            filename = each.__str__()

            if each.parent().exists():
                pass
            else:
                each.parent().mkdir()

            with each.open('r') as fr:
                collector = DocStringsCollector()
                mod = ast.parse(fr.read())
                collector.visit(mod)

            mod_name, _ = splitext(each.relative())

            for idx, [fn_name, lineno, title, prepare_code,
                      test_code] in enumerate(collector.docs):

                print(f'tests of {mod_name}.{title or fn_name} started...')

                context = {'self': self}
                prepare_code = dedent_all(prepare_code)
                test_code = dedent_all(test_code)
                fixer = FixLineno(lineno)
                try:
                    node = ast.parse(prepare_code, filename, mode='exec')

                    fixer.visit(node)
                    code = compile(node, filename, "exec")
                except SyntaxError as exc:
                    exc.lineno = lineno
                    exc.filename = filename
                    raise exc
                bc = Bytecode.from_code(code)
                bc.filename = filename
                bc.first_lineno = lineno
                exec(bc.to_code(), context)

                # not correct but as a workaround

                fixer = FixLineno(lineno + test_code.count('\n'))
                try:
                    node = parse(test_code, filename).result
                    # pprint(node)
                    fixer.visit(node)
                    code = py_compile(node, filename, is_entrypoint=True)
                except SyntaxError as exc:
                    exc.lineno = lineno
                    exc.filename = filename
                    raise exc
                bc = Bytecode.from_code(code)
                bc.filename = filename
                bc.first_lineno = lineno
                code_obj = bc.to_code()

                exec(code_obj, context)
                print(f'tests of {mod_name}.{title or fn_name} passed.')


if __name__ == '__main__':
    unittest.main()
