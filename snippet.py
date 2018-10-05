"""
Update note: Never use this module to test your emit functions.
Use the file `auto_test.py` in the same directory instead.

"""

import ast
import types

from astpretty import pprint
from yapypy.extended_python.parser import parse
from yapypy.extended_python.symbol_analyzer import ASTTagger, SymTable, to_tagged_ast, Tag
from yapypy.extended_python.py_compile import py_compile
import dis
from bytecode import Bytecode, UNSET, Label, BasicBlock, ConcreteBytecode, ControlFlowGraph


def parse_expr(expr_code):
    return parse(expr_code).result.body[0].value


def dump_bytecode(bytecode, *, lineno=False, print=print):
    def format_line(index, line):
        nonlocal cur_lineno, prev_lineno
        if lineno:
            if cur_lineno != prev_lineno:
                line = 'L.% 3s % 3s: %s' % (cur_lineno, index, line)
                prev_lineno = cur_lineno
            else:
                line = '      % 3s: %s' % (index, line)
        else:
            line = line
        return line

    def format_instr(instr, labels=None):
        text = instr.name
        arg = instr._arg
        if arg is not UNSET:
            if isinstance(arg, Label):
                try:
                    arg = '<%s>' % labels[arg]
                except KeyError:
                    arg = '<error: unknown label>'
            elif isinstance(arg, BasicBlock):
                try:
                    arg = '<%s>' % labels[id(arg)]
                except KeyError:
                    arg = '<error: unknown block>'
            else:
                arg = repr(arg)
            text = '%s %s' % (text, arg)
        return text

    indent = ' ' * 4

    cur_lineno = bytecode.first_lineno
    prev_lineno = None

    if isinstance(bytecode, ConcreteBytecode):
        offset = 0
        for instr in bytecode:
            fields = []
            if instr.lineno is not None:
                cur_lineno = instr.lineno
            if lineno:
                fields.append(format_instr(instr))
                line = ''.join(fields)
                line = format_line(offset, line)
            else:
                fields.append("% 3s    %s" % (offset, format_instr(instr)))
                line = ''.join(fields)
            print(line)

            offset += instr.size
    elif isinstance(bytecode, Bytecode):
        labels = {}
        for index, instr in enumerate(bytecode):
            if isinstance(instr, Label):
                labels[instr] = 'label_instr%s' % index

        for index, instr in enumerate(bytecode):
            if isinstance(instr, Label):
                label = labels[instr]
                line = "%s:" % label
                if index != 0:
                    print()
            else:
                if instr.lineno is not None:
                    cur_lineno = instr.lineno
                line = format_instr(instr, labels)
                line = indent + format_line(index, line)
            print(line)
        print()
    elif isinstance(bytecode, ControlFlowGraph):
        labels = {}
        for block_index, block in enumerate(bytecode, 1):
            labels[id(block)] = 'block%s' % block_index

        for block_index, block in enumerate(bytecode, 1):
            print('%s:' % labels[id(block)])
            prev_lineno = None
            for index, instr in enumerate(block):
                if instr.lineno is not None:
                    cur_lineno = instr.lineno
                line = format_instr(instr, labels)
                line = indent + format_line(index, line)
                print(line)
            if block.next_block is not None:
                print(indent + "-> %s" % labels[id(block.next_block)])
            print()
    else:
        raise TypeError("unknown bytecode class")


# stmt = parse("""
# print(1)
# def f(x):
#     a = 1
#     def g(y):
#         a + 1
#         def u(z):
#             k = 1
#             v + k
#     v = 3
#     k = 4
# """).result
#
# res: Tag = to_tagged_ast(stmt)
# print(res.tag.show_resolution())
#
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
    # dump_bytecode(Bytecode.from_code(code), print=print)
    # for each in code.co_consts:
    #     if isinstance(each, types.CodeType):
    #         dis_code(each, f)


def case(code, ctx, debug=False):
    stmt = parse(code).result
    code_obj = py_compile(stmt)
    if debug:
        code_obj2 = compile(code, "", "exec")
        with open('_yapypy_bc',
                  'w') as yapypy_bc, open('yapypy_info',
                                          'w') as yapypy_info, open(
                                              'cpy_bc', 'w') as cpy_bc, open(
                                                  'cpy_info', 'w') as cpy_info:

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
print({1: 2 for i in range(10)})
assert tuple(i for i in range(10) if i % 2 if i > 6) == (7, 9)
assert tuple((i, j) for i in range(10) if i < 8 for j in  range(5) if i % 2 if i > 6 ) == ((7, 0), (7, 1), (7, 2), (7, 3), (7, 4))
async def f():
    return (i async for i in S())

it = to_t(get_event_loop().run_until_complete(f()))
assert dict(zip(it, it)) == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
async def f():
    return ((i, i % 5) async for i in S() if i > 3)
it = to_t(get_event_loop().run_until_complete(f()))
assert tuple(it) == ((4, 4), (5, 0), (6, 1), (7, 2), (8, 3), (9, 4), (10, 0))
print(it)
    """,
    ctx,
    debug=False)

# case(
#     """
# async def f():
#     return (i % 5 async for i in S() if i > 3)
# print(to_t(get_event_loop().run_until_complete(f())))
#     """,
#     ctx,
#     debug=False)

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
