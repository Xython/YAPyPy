from bytecode import BasicBlock

from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.IfExp)
def py_emit(node: ast.IfExp, ctx: Context):
    """
    title: IfExp
    test:
    >>> a = 1 if 1 else 2
    >>> assert a == 1
    >>> a = 1 if 0 else 2
    >>> assert a == 2
    """
    py_emit(node.test, ctx)
    else_label = Label()
    out_label = Label()
    ctx.bc.append(Instr("POP_JUMP_IF_FALSE", else_label, lineno=node.lineno))
    py_emit(node.body, ctx)
    ctx.bc.append(Instr("JUMP_FORWARD", out_label, lineno=node.lineno))
    ctx.bc.append(else_label)
    py_emit(node.orelse, ctx)
    ctx.bc.append(out_label)


@py_emit.case(ast.If)
def py_emit(node: ast.If, ctx: Context):
    """
    title: If
    test:
    >>> x = 0
    >>> if 1:
    >>>     x = 1
    >>> assert x == 1

    >>> if 0:
    >>>     x = 2
    >>> else:
    >>>     x = 3
    >>> assert x == 3

    >>> if 0 or "s":
    >>>     x = 4
    >>> assert x == 4

    >>> if 0:
    >>>     x = 5
    >>> elif ...:
    >>>     x = 6
    >>> assert x == 6

    >>> a, b, c, d = (0, 0, 0, 7)
    >>> if a:
    >>>     x = a
    >>>     x = a
    >>> elif b:
    >>>     x = b
    >>> elif c:
    >>>     x = c
    >>> else:
    >>>     a = 1
    >>>     b = 2
    >>>     c = 3
    >>>     d = 4
    >>>     x = d
    >>> assert a, b, c, d, x == 1, 2, 3, 4, d
    """

    is_const = False
    kinds = [
        ast.Constant,
        ast.Num,
        ast.Str,
        ast.Bytes,
        ast.Ellipsis,
        ast.NameConstant,
    ]
    is_const = any([isinstance(node.test, kind) for kind in kinds])
    if isinstance(node.test, ast.Name):
        if node.test.id == "__debug__":
            is_const = True
    const_value = None
    if is_const:
        if isinstance(node.test, ast.Constant):
            const_value = node.test.value
        elif isinstance(node.test, ast.Num):
            const_value = node.test.n
        elif isinstance(node.test, ast.Str):
            const_value = node.test.s
        elif isinstance(node.test, ast.Bytes):
            const_value = node.test.s
        elif isinstance(node.test, ast.Ellipsis):
            const_value = ...
        elif isinstance(node.test, ast.NameConstant):
            const_value = node.test.value
        elif isinstance(node.test, ast.Name):
            const_value = __debug__  #
        else:
            raise TypeError

    if is_const:
        if const_value:
            for each in node.body:
                py_emit(each, ctx)
        else:
            for each in node.orelse:
                py_emit(each, ctx)
    else:
        out_label = Label()
        else_lable = Label()
        py_emit(node.test, ctx)
        ctx.bc.append(Instr("POP_JUMP_IF_FALSE", else_lable, lineno=node.lineno))
        for each in node.body:
            py_emit(each, ctx)
        has_orelse = False
        if node.orelse:
            has_orelse = True
            ctx.bc.append(Instr("JUMP_FORWARD", out_label, lineno=node.lineno))
            ctx.bc.append(else_lable)
            for each in node.orelse:
                py_emit(each, ctx)
        if has_orelse:
            ctx.bc.append(out_label)
        else:
            ctx.bc.append(else_lable)


@py_emit.case(ast.While)
def py_emit(node: ast.While, ctx: Context):
    """
    title: while
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> i = 0
    >>> while i < 10 and i != 5:
    >>>     i+=1
    >>> self.assertEqual(i, 5)

    >>> s = 0
    >>> a = 0
    >>> while a < 3:
    >>>     a += 1
    >>>     s += a
    >>> self.assertEqual(s, 1 + 2 + 3)

    >>> s = 0
    >>> a = 0
    >>> while a < 3:
    >>>     a += 1
    >>>     s += a
    >>> else:
    >>>     s = -1
    >>> self.assertEqual(s, -1)
    """
    while_loop_with_orelse_out = Label()
    while_iter_in = Label()
    while_iter_out = Label()
    ctx.push_current_block(BlockType.LOOP, while_iter_in)

    ctx.bc.append(SETUP_LOOP(while_loop_with_orelse_out, lineno=node.lineno))
    ctx.bc.append(while_iter_in)
    py_emit(node.test, ctx)
    ctx.bc.append(POP_JUMP_IF_FALSE(while_iter_out, lineno=node.lineno))
    for expr in node.body:
        py_emit(expr, ctx)

    ctx.bc.append(JUMP_ABSOLUTE(while_iter_in, lineno=node.lineno))
    ctx.bc.append(while_iter_out)
    ctx.bc.append(POP_BLOCK(lineno=node.lineno))

    ctx.pop_current_block(BlockType.LOOP, node.lineno)

    for each in node.orelse:
        py_emit(each, ctx)
    ctx.bc.append(while_loop_with_orelse_out)


@py_emit.case(ast.For)
def py_emit(node: ast.For, ctx: Context):
    """
    title: for
    prepare:
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> s = 0
    >>> for x in [1, 2, 3]:
    >>>     s += x
    >>> self.assertEqual(s, 1 + 2 + 3)

    >>> s = 0
    >>> for x in [1, 2, 3]:
    >>>     s += x
    >>> else:
    >>>     s = -1
    >>> self.assertEqual(s, -1)

    >>> s = 0
    >>> a = [1, 2, 3]
    >>> for x in [*a, 4]:
    >>>     s += x
    >>> self.assertEqual(s, 1 + 2 + 3 + 4)

    >>> s = 0
    >>> for k, v in [(1, 2), (3, 4)]:
    >>>     s += k
    >>>     s += v
    >>> self.assertEqual(s, 1 + 2 + 3 + 4)
    """

    for_loop_with_orelse_out = Label()
    for_iter_in = Label()
    for_iter_out = Label()
    ctx.push_current_block(BlockType.LOOP, for_iter_in)

    ctx.bc.append(SETUP_LOOP(for_loop_with_orelse_out, lineno=node.lineno))
    py_emit(node.iter, ctx)
    ctx.bc.append(GET_ITER(lineno=node.lineno))
    ctx.bc.append(for_iter_in)
    ctx.bc.append(FOR_ITER(for_iter_out, lineno=node.lineno))
    py_emit(node.target, ctx)

    for each in node.body:
        py_emit(each, ctx)
    ctx.bc.append(JUMP_ABSOLUTE(for_iter_in, lineno=node.lineno))
    ctx.bc.append(for_iter_out)
    ctx.bc.append(POP_BLOCK(lineno=node.lineno))

    ctx.pop_current_block(BlockType.LOOP, node.lineno)

    for each in node.orelse:
        py_emit(each, ctx)
    ctx.bc.append(for_loop_with_orelse_out)


@py_emit.case(ast.Break)
def py_emit(node: ast.Break, ctx: Context):
    """
    title: break
    prepare:
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> s = 0
    >>> for x in [1, 2, 3, 4]:
    >>>     if x == 3:
    >>>         break
    >>>     s += x
    >>> else:
    >>>     s = -1
    >>> self.assertEqual(s, 1 + 2)

    >>> s = 0
    >>> a = 0
    >>> while a < 10:
    >>>     a += 1
    >>>     if a == 4:
    >>>         break
    >>>     s += a
    >>> else:
    >>>     s = -1
    >>> self.assertEqual(s, 1 + 2 + 3)

    >>> s = 0
    >>> for x in [1, 2, 3]:
    >>>     for y in [1, 2, 3, 4]:
    >>>         if y > 1:
    >>>             break
    >>>         s += y
    >>>     s += x
    >>> self.assertEqual(s, 1 + 1 + 1 + 2 + 1 + 3)

    >>> s = 0
    >>> for x in [1, 2, 3]:
    >>>     y = 0
    >>>     while y < 4:
    >>>         y += 1
    >>>         if y > 1:
    >>>             break
    >>>         s += y
    >>>     s += x
    >>> self.assertEqual(s, 1 + 1 + 1 + 2 + 1 + 3)
    """
    ctx.bc.append(Instr('BREAK_LOOP', lineno=node.lineno))


@py_emit.case(ast.Continue)
def py_emit(node: ast.Continue, ctx: Context):
    """
    title: continue
    prepare:
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> s = 0
    >>> for x in [1, 2, 3, 4]:
    >>>     if x == 2:
    >>>         continue
    >>>     s += x
    >>> self.assertEqual(s, 1 + 3 + 4)

    >>> s = 0
    >>> a = 0
    >>> while a < 4:
    >>>     a += 1
    >>>     if a == 2:
    >>>         continue
    >>>     s += a
    >>> self.assertEqual(s, 1 + 3 + 4)

    >>> s = 0
    >>> for x in [1, 2, 3, 4]:
    >>>     if x == 2:
    >>>         continue
    >>>     s += x
    >>> else:
    >>>     s = -1
    >>> self.assertEqual(s, -1)

    >>> s = 0
    >>> a = 0
    >>> while a < 4:
    >>>     a += 1
    >>>     if a == 2:
    >>>         continue
    >>>     s += a
    >>> else:
    >>>     s = -1
    >>> self.assertEqual(s, -1)

    >>> s = 0
    >>> for x in [1, 2, 3]:
    >>>     for y in [4, 5, 6]:
    >>>         if y == 5:
    >>>             continue
    >>>         s += y
    >>>     if x == 2:
    >>>         continue
    >>>     s += x
    >>> self.assertEqual(s, 4+6+1 + 4+6 + 4+6+3)


    >>> s = 0
    >>> for x in [1, 2, 3]:
    >>>     y = 3
    >>>     while y < 6:
    >>>         y += 1
    >>>         if y == 5:
    >>>             continue
    >>>         s += y
    >>>     if x == 2:
    >>>         continue
    >>>     s += x
    >>> self.assertEqual(s, 4+6+1 + 4+6 + 4+6+3)

    """
    blktype, label = ctx.get_current_block()

    if blktype == BlockType.LOOP:
        _, label = ctx.get_current_block()
        ctx.bc.append(JUMP_ABSOLUTE(label, lineno=node.lineno))

    elif blktype == BlockType.EXCEPT or blktype == BlockType.FINALLY_TRY:
        blkstack = ctx.get_block_stack()
        i = len(blkstack) - 1
        while (i >= 0 and blkstack[i] != BlockType.LOOP):
            i -= 1
            blktype, _ = blkstack[i]
            if blktype == BlockType.LOOP:
                break
            if blkstack[i] == BlockType.FINALLY_END:
                exc = SyntaxError()
                exc.lineno = node.lineno
                exc.msg = "'continue' not supported inside 'finally' clause"
                raise exc

        if i < 0:
            exc = SyntaxError()
            exc.lineno = node.lineno
            exc.msg = "'continue' not properly in loop"
            raise exc

        _, label = blkstack[i]
        ctx.bc.append(CONTINUE_LOOP(label, lineno=node.lineno))

    elif blktype == BlockType.FINALLY_END:
        exc = SyntaxError()
        exc.msg = "'continue' not supported inside 'finally' clause"
        exc.lineno = node.lineno
        raise exc


@py_emit.case(ast.With)
def py_emit(node: ast.With, ctx: Context):
    """
    title: With
    prepare:
    >>> import os
    >>> import unittest
    >>> self: unittest.TestCase
    test:
    >>> with open(os.devnull, "w") as fp, open(os.devnull, "w"), open(os.devnull, "w") as fpp:
    >>>     fp.write("emmm")
    >>>     fpp.write("ummm")
    >>>     assert not fp.closed and not fpp.closed
    >>> assert fp.closed and fpp.closed, True
    
    >>> a = -1
    >>> for i in range(10):
    >>>     with open(os.devnull, "w") as fp:
    >>>         assert not fp.closed
    >>>         a = i
    >>>         break
    >>> assert not a and fp.closed, True

    >>> s = 0
    >>> for x in [1, 2, 3, 4]:
    >>>     with open(os.devnull, "w") as fp:
    >>>         if x == 3:
    >>>             continue
    >>>         s += x
    >>> self.assertEqual(s, 1 + 2 + 4)
    """

    flabel_stack = []
    for each in node.items:
        finally_label = Label()
        flabel_stack.append(finally_label)
        py_emit(each.context_expr, ctx)
        ctx.bc.append(Instr("SETUP_WITH", finally_label, lineno=node.lineno))
        ctx.push_current_block(BlockType.FINALLY_TRY)
        if each.optional_vars:
            py_emit(each.optional_vars, ctx)
        else:
            ctx.bc.append(Instr("POP_TOP", lineno=node.lineno))

    for each in node.body:
        py_emit(each, ctx)

    while flabel_stack:
        ctx.bc.append(Instr("POP_BLOCK", lineno=node.lineno))
        ctx.pop_current_block(BlockType.FINALLY_TRY, node.lineno)

        ctx.bc.append(Instr("LOAD_CONST", None, lineno=node.lineno))
        finally_label = flabel_stack.pop(-1)
        ctx.push_current_block(BlockType.FINALLY_END, finally_label)
        ctx.bc.append(finally_label)
        ctx.bc.append(Instr("WITH_CLEANUP_START", lineno=node.lineno))
        ctx.bc.append(Instr("WITH_CLEANUP_FINISH", lineno=node.lineno))
        ctx.bc.append(Instr("END_FINALLY", lineno=node.lineno))
        ctx.pop_current_block(BlockType.FINALLY_END, node.lineno)

