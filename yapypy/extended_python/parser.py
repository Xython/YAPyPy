import tokenize
from rbnf.core.Tokenizer import Tokenizer
from rbnf.core.CachingPool import ConstStrPool
from rbnf.core.State import State
from rbnf.easy import Language, build_parser, build_language, ze
from keyword import kwlist
from yapypy.extended_python.grammar import RBNF
from yapypy.extended_python import helper, extended_ast

import ast
import typing as t
import io
cast = ConstStrPool.cast_to_const


def to_rbnf_token(tk: tokenize.TokenInfo) -> Tokenizer:
    name = cast(tokenize.tok_name[tk.type])
    if name == 'NAME' and tk.string in kwlist:
        value = cast(tk.string)
        name = cast('KEYWORD')
    else:
        value = cast(tk.string) if name not in ('NAME', 'STRING',
                                                'NUMBER') else tk.string
    return Tokenizer(name, value, *tk.start)


tokens_to_ignore = (tokenize.COMMENT, tokenize.ENCODING, tokenize.NL)


def not_to_ignore(tk: tokenize.TokenInfo) -> bool:
    return tk.type not in tokens_to_ignore


def lex(text: t.Union[str, bytes]):
    if isinstance(text, str):
        text = text.encode()
    stream = io.BytesIO(text)
    return map(to_rbnf_token,
               filter(not_to_ignore, tokenize.tokenize(stream.__next__)))


python = Language('python')
python.namespace.update({
    **extended_ast.__dict__,
    **helper.__dict__,
    **ast.__dict__
})
build_language(RBNF, python, '<grammar>')
python_parser = python.named_parsers['file_input']


def _find_error(source_code, tokens, state):
    def _find_nth(string: str, element, nth: int = 0):
        _pos: int = string.find(element)
        if _pos is -1:
            return 0

        while nth:
            _pos = string.index(element, _pos) + 1
            nth -= 1
        return _pos

    if not tokens:
        return 0, source_code[:20]

    if state.end_index < len(tokens):
        max_fetched = state.max_fetched
        if max_fetched >= len(tokens):
            tk = tokens[-1]
        else:
            tk: Tokenizer = tokens[max_fetched]
        lineno, colno = tk.lineno, tk.colno
        pos = _find_nth(source_code, '\n', lineno - 1) + colno
        left = max(0, pos - 25)
        where = source_code[left:min(pos + 25, len(source_code))]
        return left, where
    raise RuntimeError


def parse(text, filename=None):
    tokens = tuple(lex(text))
    state = State(python.implementation, filename=filename)
    try:
        parsed = python_parser.match(tokens, state)
        return ze.ResultDescription(state, parsed.value, tokens)
    except SyntaxError as e:
        e.filename = filename or '<unknown>'
        e.offset, e.text = _find_error(text, tokens, state)
        e.__traceback__ = None
        raise e
