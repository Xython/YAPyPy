import typing as t
from rbnf.core.State import State
from rbnf.std.common import recover_codes
from rbnf.core.Tokenizer import Tokenizer


def is_indented(it: Tokenizer, state: State):
    mark: Tokenizer = state.ctx.get('mark')
    return mark.colno < it.colno


class Value(t.NamedTuple):
    v: str


class Field(t.NamedTuple):
    name: str
    type: Value
    option: t.List[str]
    default: t.Optional[Value]


class Primary(t.NamedTuple):
    name: str
    type: Value
    option: t.List[str]
    default: t.Optional[Value]


class Table(t.NamedTuple):
    name: str
    primary: Field
    fields: t.List[Field]
    reprs: t.List[str]


class Engine(t.NamedTuple):
    configs: dict


class Relation(t.NamedTuple):
    left: str
    right: str
    weight: t.Tuple[int, int]
    fields: t.List[Field]


class Python(t.NamedTuple):
    codes: str
