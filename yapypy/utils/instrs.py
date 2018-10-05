from bytecode import Instr, Label, Compare


def LOAD_ATTR(attr: str, *, lineno=None):
    return Instr('LOAD_ATTR', attr, lineno=lineno)


def STORE_ATTR(attr: str, *, lineno=None):
    return Instr('STORE_ATTR', attr, lineno=lineno)


def GET_ANEXT(*, lineno=None):
    return Instr("GET_ANEXT", lineno=lineno)


def SETUP_EXCEPT(label: Label, *, lineno=None):
    return Instr("SETUP_EXCEPT", label, lineno=lineno)


def SETUP_FINALLY(label: Label, *, lineno=None):
    return Instr("SETUP_FINALLY", label, lineno=lineno)


def YIELD_VALUE(*, lineno=None):
    return Instr("YIELD_VALUE", lineno=lineno)


def GET_AITER(*, lineno=None):
    return Instr("GET_AITER", lineno=lineno)


def GET_AWAITABLE(*, lineno=None):
    return Instr("GET_AWAITABLE", lineno=lineno)


def END_FINALLY(*, lineno=None):
    return Instr("END_FINALLY", lineno=lineno)


def COMPARE_OP(arg: Compare, *, lineno=None):
    return Instr("COMPARE_OP", arg, lineno=lineno)


def POP_EXCEPT(*, lineno=None):
    return Instr("POP_EXCEPT", lineno=lineno)


def YIELD_FROM(*, lineno=None):
    return Instr("YIELD_FROM", lineno=lineno)


def DELETE_ATTR(attr: str, *, lineno=None):
    return Instr('DELETE_ATTR', attr, lineno=lineno)


def CALL_FUNCTION(n: int, *, lineno=None):
    return Instr('CALL_FUNCTION', n, lineno=lineno)


def RAISE_VARARGS(n: int, lineno=None):
    return Instr('RAISE_VARARGS', n, lineno=lineno)


def POP_JUMP_IF_TRUE(label: Label, lineno=None):
    return Instr('POP_JUMP_IF_TRUE', label, lineno=lineno)


def UNPACK_EX(arg: int, lineno=None):
    return Instr('UNPACK_EX', arg, lineno=lineno)


def LOAD_GLOBAL(name: str, lineno=None):
    return Instr('LOAD_GLOBAL', name, lineno=lineno)


def LOAD_CONST(var: object, *, lineno=None):
    return Instr('LOAD_CONST', var, lineno=lineno)


def LOAD_FAST(name: str, *, lineno=None):
    return Instr('LOAD_FAST', name, lineno=lineno)


def STORE_FAST(name: str, *, lineno=None):
    return Instr('STORE_FAST', name, lineno=lineno)


def BUILD_STRING(n: int, *, lineno=None):
    return Instr('BUILD_STRING', n, lineno=lineno)


def UNPACK_SEQUENCE(n: int, *, lineno=None):
    return Instr('UNPACK_SEQUENCE', n, lineno=lineno)


def BUILD_TUPLE(n: int, *, lineno=None):
    return Instr('BUILD_TUPLE', n, lineno=lineno)


def BUILD_TUPLE_UNPACK(n: int, *, lineno=None):
    return Instr('BUILD_TUPLE_UNPACK', n, lineno=lineno)


def BUILD_LIST(n: int, *, lineno=None):
    return Instr('BUILD_LIST', n, lineno=lineno)


def BUILD_LIST_UNPACK(n: int, *, lineno=None):
    return Instr('BUILD_LIST_UNPACK', n, lineno=lineno)


def BUILD_SET(n: int, *, lineno=None):
    return Instr('BUILD_SET', n, lineno=lineno)


def BUILD_SLICE(n: int, *, lineno=None):
    return Instr('BUILD_SLICE', n, lineno=lineno)


def STORE_SUBSCR(*, lineno=None):
    return Instr('STORE_SUBSCR', lineno=lineno)


def BINARY_SUBSCR(*, lineno=None):
    return Instr('BINARY_SUBSCR', lineno=lineno)


def DELETE_SUBSCR(*, lineno=None):
    return Instr('DELETE_SUBSCR', lineno=lineno)


def ROT_TWO(*, lineno=None):
    return Instr('ROT_TWO', lineno=lineno)


def ROT_THREE(*, lineno=None):
    return Instr('ROT_THREE', lineno=lineno)


def RETURN_VALUE(*, lineno=None):
    return Instr('RETURN_VALUE', lineno=lineno)


def MAKE_FUNCTION(n: int, *, lineno=None):
    return Instr("MAKE_FUNCTION", n, lineno=lineno)


def JUMP_ABSOLUTE(label: Label, *, lineno=None):
    return Instr("JUMP_ABSOLUTE", label, lineno=lineno)


def GET_ITER(*, lineno=None):
    return Instr("GET_ITER", lineno=lineno)


def FOR_ITER(label: Label, *, lineno=None):
    return Instr("FOR_ITER", label, lineno=lineno)


def POP_BLOCK(*, lineno=None):
    return Instr("POP_BLOCK", lineno=lineno)


def POP_JUMP_IF_FALSE(label: Label, *, lineno=None):
    return Instr("POP_JUMP_IF_FALSE", label, lineno=lineno)


def JUMP_FORWARD(label: Label, *, lineno=None):
    return Instr("JUMP_FORWARD", label, lineno=lineno)


def JUMP_IF_FALSE_OR_POP(label: Label, *, lineno=None):
    return Instr("JUMP_IF_FALSE_OR_POP", label, lineno=lineno)


def SETUP_LOOP(label: Label, *, lineno=None):
    return Instr("SETUP_LOOP", label, lineno=lineno)


def DUP_TOP(*, lineno=None):
    return Instr('DUP_TOP', lineno=lineno)


def DUP_TOP_TWO(*, lineno=None):
    return Instr('DUP_TOP_TWO', lineno=lineno)


def POP_TOP(*, lineno=None):
    return Instr('POP_TOP', lineno=lineno)


def SETUP_ANNOTATIONS(*, lineno=None):
    return Instr('SETUP_ANNOTATIONS', lineno=lineno)


def STORE_ANNOTATION(n, *, lineno=None):
    return Instr('STORE_ANNOTATION', n, lineno=lineno)
