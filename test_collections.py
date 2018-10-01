from kizmi.utils.namedlist import as_namedlist, trait, INamedList
from typing import NamedTuple
from timeit import timeit


class S(INamedList, metaclass=trait(as_namedlist)):
    a: int
    b: int
    c: int

