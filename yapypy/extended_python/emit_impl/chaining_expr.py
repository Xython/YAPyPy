from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Call)
def py_emit(node: ast.Call, ctx: Context):
    """
    title: call
    test:
     >>> a = 'a',
     >>> b = 'b',
     >>> c = 'c',
     >>> d = {'d': 0}
     >>> e = {'e': 1}
     >>> g = {'g': 2}
     >>> x = {'x': 3}
     >>> y = {'y': 4}
     >>>
     >>>
     >>> def f(*args, **kwargs):
     >>>     print(args, kwargs)
     >>>
     >>> f(1, c=3, d=4)
     >>>
     >>> f(1, 2, *a, 3, *b, *c, 4, **e, **g)
     >>> f(1, *b, d=4)
     >>>
     >>> f(1, 2, 3, a=1, b=2)
     >>> f(*a, 1, *a, 2, 3, *b, *e, 3, *c, **x, **y)
     >>> f(*a, 1, *a, 2, *b, 3, *c, **x, **y)
     >>> f(1, *a, 2, *b, 3, *c, **x, **y)
     >>> f(1, 2, **e, **d)
     >>> f(**e, **d)
     >>> f(*b, **d)
     >>> f(*b)
     >>> f(a, *b)
     >>> f(1, 2, *c, **d, **e)
     >>> f(1, 2, *c)
     >>> f(1, 2, y=1, *x, a=1, b=2, c=3, **d)
     >>> f(1, 2, y=1, *x, a=1, b=2, c=3, **d, e=4)
    """
    py_emit(node.func, ctx)

    has_star = False
    has_key = False
    has_star_star = False

    for each in node.args:
        if isinstance(each, ast.Starred):
            has_star = True
            break
    for each in node.keywords:
        if each.arg:
            has_key = True
            break
    for each in node.keywords:
        if each.arg is None:
            has_star_star = True
            break

    # positional arguments
    if has_star or has_star_star:
        arg_count = 0
        arg_tuple_count = 0
        for each in node.args:
            if not isinstance(each, ast.Starred):
                py_emit(each, ctx)
                arg_count += 1
            else:
                if arg_count:
                    ctx.bc.append(
                        Instr("BUILD_TUPLE", arg_count, lineno=node.lineno))
                    arg_tuple_count += 1
                    arg_count = 0
                py_emit(each.value, ctx)
                arg_tuple_count += 1

        if arg_count:
            ctx.bc.append(Instr("BUILD_TUPLE", arg_count, lineno=node.lineno))
            arg_tuple_count += 1

        if arg_tuple_count > 1:
            ctx.bc.append(
                Instr(
                    "BUILD_TUPLE_UNPACK_WITH_CALL",
                    arg_tuple_count,
                    lineno=node.lineno))
        elif arg_tuple_count == 1:
            pass
        elif arg_tuple_count == 0:
            ctx.bc.append(Instr("BUILD_TUPLE", 0, lineno=node.lineno))
    else:
        for each in node.args:
            py_emit(each, ctx)

    # keyword arguments
    if has_star or has_star_star:
        karg_pack_count = 0
        keys = []
        values = []
        karg_count = 0
        # use dummy node handle trailing keyword arguments
        dummy_node = ast.keyword(arg=None)
        node.keywords.append(dummy_node)
        for each in node.keywords:
            if each.arg:
                keys.append(each.arg)
                values.append(each.value)
                karg_count += 1
            else:
                if karg_count:
                    karg_pack_count += 1
                    if karg_count > 1:
                        for value in values:
                            py_emit(value, ctx)

                        ctx.bc.append(
                            Instr(
                                "LOAD_CONST",
                                tuple(keys),
                                lineno=node.lineno,
                            ), )

                        ctx.bc.append(
                            Instr(
                                "BUILD_CONST_KEY_MAP",
                                karg_count,
                                lineno=node.lineno,
                            ), )
                    elif karg_count == 1:
                        ctx.bc.append(
                            Instr("LOAD_CONST", keys[0], lineno=node.lineno))
                        py_emit(values[0], ctx)
                        ctx.bc.append(
                            Instr("BUILD_MAP", 1, lineno=node.lineno))
                    keys = []
                    values = []
                    karg_count = 0
                if each is dummy_node:
                    break
                py_emit(each.value, ctx)
                karg_pack_count += 1
        node.keywords.pop(-1)  # pop dummy node
        if karg_pack_count > 1:
            ctx.bc.append(
                Instr(
                    "BUILD_MAP_UNPACK_WITH_CALL",
                    karg_pack_count,
                    lineno=node.lineno))
    else:
        keys = []
        for each in node.keywords:
            py_emit(each.value, ctx)
            keys.append(each.arg)
        if keys:
            ctx.bc.append(Instr("LOAD_CONST", tuple(keys), lineno=node.lineno))

    if has_star or has_star_star:
        ctx.bc.append(
            Instr(
                "CALL_FUNCTION_EX",
                has_star_star | has_key,
                lineno=node.lineno))
    elif has_key:
        ctx.bc.append(
            Instr(
                "CALL_FUNCTION_KW",
                len(node.args) + len(node.keywords),
                lineno=node.lineno))
    else:
        ctx.bc.append(
            Instr('CALL_FUNCTION', len(node.args), lineno=node.lineno))


@py_emit.case(ast.Compare)
def py_emit(node: ast.Compare, ctx: Context):
    """
    title:compare
    test:
    >>> 1 == 1
    >>> 1 != 1
    >>> 1 > 1
    >>> 1 >= 2
    >>> 1 < 1
    >>> 1 <= 2
    >>> 1 is 1
    >>> 1 is not 1
    >>> 1 in range(2)
    >>> 1 not in range(3)
    >>> 1 == 1 != 2 > 1 >= 1 < 2 <= 2 is 2 is not 3 in range(3) not in range(3)
    >>> x = 3
    >>> assert 2 < x < 5
    >>> assert 2 <= x < 5 < 10
    """
    ops = {
        ast.Eq: Compare.EQ,
        ast.NotEq: Compare.NE,
        ast.Lt: Compare.LT,
        ast.LtE: Compare.LE,
        ast.Gt: Compare.GT,
        ast.GtE: Compare.GE,
        ast.Is: Compare.IS,
        ast.IsNot: Compare.IS_NOT,
        ast.In: Compare.IN,
        ast.NotIn: Compare.NOT_IN,
    }
    len_of_comparators = len(node.comparators)
    is_multiple = len_of_comparators > 1

    py_emit(node.left, ctx)
    if is_multiple:
        last_idx_of_comparators = len_of_comparators - 1
        label_rot = Label()
        label_out = Label()

        for idx in range(len_of_comparators):
            op_type = type(node.ops[idx])
            op = ops.get(op_type)
            expr = node.comparators[idx]

            py_emit(expr, ctx)
            if idx == last_idx_of_comparators:
                ctx.bc.append(Instr("COMPARE_OP", op, lineno=node.lineno))
                ctx.bc.append(JUMP_FORWARD(label_out, lineno=node.lineno))
            else:
                ctx.bc.append(DUP_TOP(lineno=node.lineno))
                ctx.bc.append(ROT_THREE(lineno=node.lineno))
                ctx.bc.append(Instr("COMPARE_OP", op, lineno=node.lineno))
                ctx.bc.append(
                    JUMP_IF_FALSE_OR_POP(label_rot, lineno=node.lineno))

        ctx.bc.append(label_rot)
        ctx.bc.append(ROT_TWO(lineno=node.lineno))
        ctx.bc.append(POP_TOP(lineno=node.lineno))
        ctx.bc.append(label_out)
    else:
        py_emit(node.comparators[0], ctx)
        op_type = type(node.ops[0])
        op = ops.get(op_type)
        ctx.bc.append(Instr("COMPARE_OP", op, lineno=node.lineno))


@py_emit.case(ast.FormattedValue)
def py_emit(node: ast.FormattedValue, ctx: Context):
    """
    title: formatted value
    test:
    >>> from datetime import datetime
    >>> p = print
    >>> A = "A"
    >>> assert f'{A}' == A
    >>> assert f'{A!r}' == "'A'"
    >>> p (f'{A!s}')
    >>> p (f'{A!a}')

    >>> p (f'{A!r:>30}')
    >>> p (f'{A!r:<30}')

    >>> p (f'{A!r:^30}')
    >>> p (f'{A!r:*^20}')

    >>> p (f'{3.14:+f}')
    >>> p (f'{3.14:f}')
    >>> p (f'{3.14:-f}')
    >>> a = 233
    >>> p (f'{a:d} {a:x} {a:o} {a:b}')
    >>> p (f'{a:d} {a:#x} {a:#o} {a:#b}')

    >>> p (f'{123456789:,}')
    >>> p (f'{19/22:.2%}')

    >>> p (f'{datetime.now():%Y-%m-%d %H:%M:%S}' )
    """
    conversion = node.conversion
    format_spec = node.format_spec
    value = node.value
    maps = {
        97: 3,  # ascii
        114: 2,  # repr
        115: 1,  # str
        -1: 0,  # None
    }

    py_emit(value, ctx)
    flags = maps[conversion]

    if format_spec is not None:
        py_emit(format_spec, ctx)
        flags += 4

    ctx.bc.append(Instr("FORMAT_VALUE", flags, lineno=node.lineno))
