from collections import Iterable
from .err import ArgumentError


def is_unque(collections: Iterable):
    count = set()
    for each in collections:
        if each in count:
            return False
        count.add(each)
    return True


class ClassProperty:
    def __init__(self, method):
        self.method = method

    def __get__(self, _, instance_cls):
        return self.method(instance_cls)


def partition(lst, cond):
    ret_a = []
    ret_b = []

    append_a = ret_a.append
    append_b = ret_b.append

    for each in lst:
        if cond(each):
            append_a(each)
            continue
        append_b(each)
    return ret_a, ret_b


def auto_doc(f):
    def app(*args):
        return f.__doc__

    app.__doc__ = f.__doc__
    return app


def crate(cls, **kwargs):
    inst = cls()
    for k, v in kwargs.items():
        setattr(inst, k, v)
    return inst


def shape_as(reshape_template, recursive_types=(list, tuple, set)):
    def _reshape(reshape_template_, recursive_types_):

        fn_lst = [
            _reshape(e, recursive_types_)
            if e.__class__ in recursive_types_ else next
            for e in reshape_template_
        ]
        ret_cls = reshape_template_.__class__

        def apply(itor):
            # noinspection PyCallingNonCallable,PyCallingNonCallable
            return ret_cls(fn(itor) for fn in fn_lst)

        return apply

    _apply = _reshape(reshape_template, set(recursive_types))

    def apply(seq):
        return _apply(iter(seq))

    return apply


def map_with_shape(f, recursive_types=(list, tuple, set)):
    def apply(maybe_seq):
        if isinstance(maybe_seq, recursive_types):
            return maybe_seq.__class__(apply(e) for e in maybe_seq)
        return f(maybe_seq)

    return apply
