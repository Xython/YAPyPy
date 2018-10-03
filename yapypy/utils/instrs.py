from bytecode import Instr


def LOAD_ATTR(attr: str, *, lineno=None):
    return Instr('LOAD_ATTR', attr, lineno=lineno)


def STORE_ATTR(attr: str, *, lineno=None):
    return Instr('STORE_ATTR', attr, lineno=lineno)


def DELETE_ATTR(attr: str, *, lineno=None):
    return Instr('DELETE_ATTR', attr, lineno=lineno)


def CALL_FUNCTION(n: int, *, lineno=None):
    return Instr('CALL_FUNCTION', n, lineno=lineno)


def RAISE_VARARGS(n: int, lineno=None):
    return Instr('RAISE_VARARGS', n, lineno=lineno)


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


def DUP_TOP(*, lineno=None):
    return Instr('DUP_TOP', lineno=lineno)


def POP_TOP(*, lineno=None):
    return Instr('POP_TOP', lineno=lineno)
