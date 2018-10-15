"""
Update note: Never use this module to test your emit functions.
Use the file `auto_test.py` in the same directory instead.

"""

import ast
import sys
import types

from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.py_compile import py_compile
from bytecode import Bytecode
import dis


def parse_expr(expr_code):
    return parse(expr_code).result.body[0].value


ctx = {}
exec(
    r"""
from asyncio import sleep, get_event_loop
class S:
  def __init__(self): self.i = 0
  def __aiter__(self): return self
  async def __anext__(self):
       if self.i < 10:
            self.i += 1
            await sleep(0.1)
            return self.i
       raise StopAsyncIteration
def to_t(aiter):
    async def _():
        d = []
        async for each in aiter:
            d.append(each)
        return tuple(d)
    return get_event_loop().run_until_complete(_())

""", ctx)


def show_code(code: types.CodeType, f, contains=()):
    if code in contains:
        return

    f.write('\n\n\n')
    f.write(code.co_name)
    f.write(':\n\n')
    dis.show_code(code, file=f)
    for each in code.co_consts:
        if isinstance(each, types.CodeType):
            show_code(each, f, (*contains, code))


def dis_code(code: types.CodeType, f):
    f.write(code.co_name)
    f.write('\n')
    # def print(*args):
    #     for each in args:
    #         f.write(str(each))
    #         f.write(' ')
    #     f.write('\n')

    dis.dis(code, file=f)
    if sys.version_info < (3, 7):
        # dump_bytecode(Bytecode.from_code(code), print=print)
        for each in code.co_consts:
            if isinstance(each, types.CodeType):
                dis_code(each, f)


def case(code, ctx, debug=False):
    stmt = parse(code).result
    code_obj = py_compile(stmt, is_entrypoint=False)

    if debug:
        code_obj2 = compile(code, "", "exec")
        with open('out_yapypy_bc.log', 'w') as yapypy_bc, open(
                'out_yapypy_info.log', 'w') as yapypy_info, open(
                    'out_cpy_bc.log', 'w') as cpy_bc, open(
                        'out_cpy_info.log', 'w') as cpy_info:

            dis_code(code_obj, yapypy_bc)
            show_code(code_obj, yapypy_info)
            dis_code(code_obj2, cpy_bc)
            show_code(code_obj2, cpy_info)

        print('python:')
        exec(Bytecode.from_code(code_obj2).to_code(), ctx or {})
        print('yapypy')
        exec(Bytecode.from_code(code_obj).to_code(), ctx or {})

    else:
        exec(code_obj, ctx)


case(
    """
def f():
    arg = 0
    def g():
        return [arg for _ in range(20)]
    return g
    
print(f()())
    """,
    ctx,
    debug=True)

# case(
#     """
# async def f():
#     return (i % 5 async for i in S())
# print(to_t(get_event_loop().run_until_complete(f())))
#     """,
#     ctx,
#     debug=False)
#
# case(
#     """
# async def f():
#     return {i % 5: i for k in range(2) async for i in S()}
# print(get_event_loop().run_until_complete(f()))
#     """,
#     ctx,
#     debug=True)

# exec(code, ctx)
# dis.dis(code.co_consts[0])
# dis.dis(code.co_consts[1])

# try:
#     parse_expr('f(a=1, b)\n')
# except SyntaxError:
#     print('good')
#
# from bytecode import Bytecode, Instr, Label
# bc = Bytecode()
# bc.append(Instr("BUILD_MAP", 0))
# bc.append(Instr("LOAD_GLOBAL", "range"))
# bc.append(Instr("LOAD_CONST", 2))
# bc.append(Instr("CALL_FUNCTION", 1, lineno=2))
#
# l1 = Label()
# l2 = Label()
# bc.append(Instr("GET_ITER"))
# bc.append(l1)
# bc.append(Instr("FOR_ITER", l2))
# bc.append(Instr("STORE_FAST", "i"))
# bc.append(Instr("LOAD_CONST", 2))
# bc.append(Instr("LOAD_CONST", 1, lineno=1))
# bc.append(Instr("MAP_ADD", 2))
# bc.append(Instr("JUMP_ABSOLUTE", l1))
# bc.append(l2)
# bc.append(Instr("RETURN_VALUE", ))
#
# code = bc.to_code()
# print(eval(code))
# dis.show_code(code)
# dis.dis(code)
