"""
INamedList is just for type hinting,
    and `INamedList is list` got a `True`,
    but we told IDE that it's a NamedTuple to
    got corresponding type hinting.
"""
from bytecode import Instr, Bytecode, CompilerFlags
from typing import NamedTuple as INamedList
import sys

globals()['INamedList'] = list
__all__ = ['metaclasses', 'as_namedlist', 'trait', 'INamedList']


def metaclasses(*clses: type, typename='metametaclass'):

    def __new__(mcs, name, base, namespace):
        bases = tuple(cls(f'{cls.__name__}{name}', base, namespace) for cls in clses)
        return type(name, bases, namespace)

    return type(typename, (type, ), dict(__new__=__new__))


def trait(*traits):

    def apply(name, bases, namespace):
        for each in traits:
            bases, namespace = each(name, bases, namespace)
        return type.__new__(type, name, bases, namespace)

    return apply


def as_namedlist(name, bases, namespace: dict):
    try:
        module = sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        module = '__main__'

    namespace = {**namespace}
    annotations: dict = namespace.get('__annotations__')

    try:
        filepath = sys.modules[module].__file__
    except (AttributeError, IndexError):
        filepath = "<unknown>"

    if annotations is not None:
        for i, (k, v) in enumerate(annotations.items()):
            if k in namespace:
                raise AttributeError

            getter_code = Bytecode()
            getter_code.filename = filepath
            getter_code.argcount = 1
            getter_code.argnames.append('self')
            getter_code.append(Instr('LOAD_FAST', 'self'))
            getter_code.append(Instr('LOAD_CONST', i))
            getter_code.append(Instr('BINARY_SUBSCR'))
            getter_code.append(Instr('RETURN_VALUE'))
            getter_code.flags = CompilerFlags.OPTIMIZED | CompilerFlags.NEWLOCALS | CompilerFlags.NOFREE
            getter_fn = property(get_func_from_code(getter_code.to_code(), k))

            setter_code = Bytecode()
            setter_code.filename = filepath
            setter_code.argcount = 2
            setter_code.argnames.extend(['self', 'value'])
            setter_code.append(Instr('LOAD_FAST', 'value'))
            setter_code.append(Instr('LOAD_FAST', 'self'))
            setter_code.append(Instr('LOAD_CONST', i))
            setter_code.append(Instr('STORE_SUBSCR'))
            setter_code.append(Instr('LOAD_CONST', None))
            setter_code.append(Instr('RETURN_VALUE'))
            setter_code.flags = CompilerFlags.OPTIMIZED | CompilerFlags.NEWLOCALS | CompilerFlags.NOFREE
            setter_fn = getter_fn.setter(get_func_from_code(setter_code.to_code(), k))
            namespace[k] = setter_fn

        init_code = Bytecode()
        init_code.name = '__init__'
        init_code.filename = filepath

        ary_num = len(annotations)
        args = list(annotations)
        init_code.argcount = ary_num + 1
        init_code.argnames.extend(['self', *args])
        if ary_num:
            init_code.append(Instr('LOAD_FAST', 'self'))
            if ary_num >= 4:
                init_code.append(Instr('DUP_TOP'))
                for i in range((ary_num - 2) // 2):
                    init_code.append(Instr('DUP_TOP_TWO'))
                if ary_num % 2:
                    init_code.append(Instr('DUP_TOP'))
            else:
                for i in range(ary_num - 1):
                    init_code.append(Instr('DUP_TOP'))

            for i in range(ary_num):
                init_code.append(Instr("LOAD_FAST", args[i]))
                init_code.append(Instr("LIST_APPEND", ary_num - i))

        init_code.append(Instr('LOAD_CONST', None))
        init_code.append(Instr('RETURN_VALUE'))

        init_code.flags = CompilerFlags.OPTIMIZED | CompilerFlags.NEWLOCALS | CompilerFlags.NOFREE

        namespace['__init__'] = get_func_from_code(init_code.to_code(), '__init__')

        fmt = '{}({})'.format(name, ', '.join(f'{arg}={{!r}}' for arg in args))
        str_code = Bytecode()
        str_code.argcount = 1
        str_code.argnames.append('self')
        str_code.append(Instr('LOAD_CONST', fmt.format))
        str_code.append(Instr('LOAD_FAST', 'self'))
        str_code.append(Instr('CALL_FUNCTION_EX', 0))
        str_code.append(Instr('RETURN_VALUE'))

        str_code.flags = CompilerFlags.OPTIMIZED | CompilerFlags.NEWLOCALS | CompilerFlags.NOFREE

        namespace['__str__'] = get_func_from_code(str_code.to_code(), '__str__')

    return bases if any(issubclass(t, list) for t in bases) else (*bases, list), namespace


def get_func_from_code(code_object, fn_name):
    executor_code = Bytecode()

    executor_code.append(Instr('LOAD_CONST', code_object))
    executor_code.append(Instr('LOAD_CONST', fn_name))
    executor_code.append(Instr('MAKE_FUNCTION', 0))
    executor_code.append(Instr('RETURN_VALUE'))

    executor_code.flags = CompilerFlags.OPTIMIZED | CompilerFlags.NEWLOCALS | CompilerFlags.NOFREE
    return eval(executor_code.to_code())
