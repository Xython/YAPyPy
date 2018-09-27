import tokenize
from rbnf.core.Tokenizer import Tokenizer
from rbnf.core.CachingPool import ConstStrPool
from rbnf.core.State import State
from rbnf.easy import Language, build_parser, build_language, ze
from keyword import kwlist
from .grammar import RBNF
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
build_language(RBNF, python, '<grammar>')
python_parser = python.named_parsers['file_input']


def parse(text, filename=None):
    tokens = tuple(lex(text))
    state = State(python.implementation, filename=filename)
    parsed = python_parser.match(tokens, state)
    return ze.ResultDescription(state, parsed.value, tokens)
