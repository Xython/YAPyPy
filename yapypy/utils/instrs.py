from bytecode import Instr


def LOAD_CONST(var: object, *, lineno=None):
    return Instr('LOAD_CONST', var, lineno=lineno)


def LOAD_FAST(name: str, *, lineno=None):
    return Instr('LOAD_FAST', name, lineno=lineno)


def BUILD_STRING(n: int, *, lineno=None):
    return Instr('BUILD_STRING', n, lineno=lineno)


def UNPACK_SEQUENCE(n: int, *, lineno=None):
    return Instr('UNPACK_SEQUENCE', n, lineno=lineno)


def BUILD_TUPLE(n: int, *, lineno=None):

    return Instr('BUILD_TUPLE', n, lineno=lineno)


def DUP_TOP(*, lineno=None):
    return Instr('DUP_TOP', lineno=lineno)
