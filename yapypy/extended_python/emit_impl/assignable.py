from yapypy.extended_python.pybc_emit import *


@py_emit.case(ast.Tuple)
def py_emit(node: ast.Tuple, ctx: Context):
    """
    title: tuple
    test:
    >>> x = 1
    >>> assert (x, 2, 3) == (1, 2, 3)
    >>> x, y = 2, 3
    >>> assert (x , y) = (2, 3)
    >>> x, *y, z = 2, 3, 5
    >>> y, = y
    >>> assert x == 2  and  y == 3 and z == 5
    >>> x, *y, z, t = 2, 3, 5, 5
    >>> assert t == 5
    >>> assert  (1, *(2, 3, 4), 5, *(6, 7), 8) == (1, 2, 3, 4, 5, 6, 7, 8)
    >>> del (x, y, z, t)
    """
    expr_ctx = type(node.ctx)

    star_indices = [
        idx for idx, each in enumerate(node.elts) if isinstance(each, ast.Starred)
    ]
    if star_indices:
        elts = node.elts
        n = len(elts)
        if expr_ctx is ast.Del:
            exc = SyntaxError()
            exc.msg = "try to delete starred expression."
            exc.lineno = node.lineno
            raise exc

        if expr_ctx is ast.Store:
            if len(star_indices) is not 1:
                exc = SyntaxError()
                exc.lineno = node.lineno
                exc.msg = f'{len(star_indices)} starred expressions in assignment'
                raise exc
            star_idx = star_indices[0]
            n_right = n - star_idx - 1
            n_left = star_idx
            unpack_arg = n_left + 256 * n_right
            ctx.bc.append(UNPACK_EX(unpack_arg, lineno=node.lineno))

            for i in range(0, star_idx):
                py_emit(elts[i], ctx)
            starred: ast.Starred = elts[star_idx]
            py_emit(starred.value, ctx)
            for i in range(star_idx + 1, n):
                py_emit(elts[i], ctx)
        else:
            intervals = [*star_indices, n][::-1]
            last = 0
            num = 0
            while intervals:
                now = intervals.pop()
                if now > last:
                    for i in range(last, now):
                        py_emit(elts[i], ctx)
                    ctx.bc.append(BUILD_TUPLE(now - last))
                    num += 1
                if intervals:  # starred item
                    py_emit(elts[now].value, ctx)
                    num += 1
                last = now + 1
            ctx.bc.append(BUILD_TUPLE_UNPACK(num))
        return

    if expr_ctx is ast.Store:
        ctx.bc.append(UNPACK_SEQUENCE(len(node.elts), lineno=node.lineno))
        for each in node.elts:
            py_emit(each, ctx)
    elif expr_ctx is ast.Del:
        for each in node.elts:
            py_emit(each, ctx)
    else:
        for each in node.elts:
            py_emit(each, ctx)

        ctx.bc.append(BUILD_TUPLE(len(node.elts), lineno=node.lineno))


@py_emit.case(ast.List)
def py_emit(node: ast.List, ctx: Context):
    """
    title: list
    test:
    >>> x = 1
    >>> assert [x, 2, 3] == [1, 2, 3]
    >>> [x, y] = [2, 3]
    >>> assert  x== 2 and y == 3
    >>> [x, [*y, z]]  = [2, [3, 5]]
    >>> y, = y
    >>> assert x == 2 and y == 3 and z == 5
    >>> [x, *y, z, t] = [2, 3, 5, 5]
    >>> assert t == 5
    >>> assert  [1, *[2, 3, 4], 5, *[6, 7], 8] == [1, 2, 3, 4, 5, 6, 7, 8]
    >>> del [x, y, z, t]
    """
    expr_ctx = type(node.ctx)

    star_indices = [
        idx for idx, each in enumerate(node.elts) if isinstance(each, ast.Starred)
    ]
    if star_indices:
        elts = node.elts
        n = len(elts)
        if expr_ctx is ast.Del:
            exc = SyntaxError()
            exc.msg = "try to delete starred expression."
            exc.lineno = node.lineno
            raise exc

        if expr_ctx is ast.Store:
            if len(star_indices) is not 1:
                exc = SyntaxError()
                exc.lineno = node.lineno
                exc.msg = f'{len(star_indices)} starred expressions in assignment'
                raise exc
            star_idx = star_indices[0]
            n_right = n - star_idx - 1
            n_left = star_idx
            unpack_arg = n_left + 256 * n_right
            ctx.bc.append(UNPACK_EX(unpack_arg, lineno=node.lineno))

            for i in range(0, star_idx):
                py_emit(elts[i], ctx)
            starred: ast.Starred = elts[star_idx]
            py_emit(starred.value, ctx)
            for i in range(star_idx + 1, n):
                py_emit(elts[i], ctx)
        else:
            intervals = [*star_indices, n][::-1]
            last = 0
            num = 0
            while intervals:
                now = intervals.pop()
                if now > last:
                    for i in range(last, now):
                        py_emit(elts[i], ctx)
                    ctx.bc.append(BUILD_LIST(now - last))
                    num += 1
                if len(intervals) > 0:  # starred item
                    py_emit(elts[now].value, ctx)
                    num += 1
                last = now + 1
            ctx.bc.append(BUILD_LIST_UNPACK(num))
        return

    if expr_ctx is ast.Store:
        ctx.bc.append(UNPACK_SEQUENCE(len(node.elts), lineno=node.lineno))

    for each in node.elts:
        py_emit(each, ctx)

    if expr_ctx is ast.Load:
        ctx.bc.append(BUILD_LIST(len(node.elts), lineno=node.lineno))


@py_emit.case(ex_ast.ExDict)
def py_emit(node: ex_ast.ExDict, ctx: Context):
    """
    title:
    test:
    >>> a = {1: 2, 3: 4}
    >>> b = {5: 6, **a, 1: 10}
    >>> assert b[5] == 6 and b[3] == 4 and b[1] == 10
    >>> b = {7: a, **b, **a}
    >>> assert b[7] is a and b[1] == 2
    >>> print(b)
    >>> {7: a, 1: c} = b
    >>> assert a == {1: 2, 3: 4} and c == 2
    >>> {7: {1: a, 3: b}, 1: c} = b
    >>> print(a, b, c)
    >>> assert a == 2 and b == 4 and c == 2
    >>> x = {1: 2, 3: 4, 5: 6}
    >>> {1:a, **kw} = x
    >>> print(a, kw)
    >>> assert a == 2 and kw == {3: 4, 5: 6}

    """
    keys = node.keys
    expr_ctx_ty = type(node.ctx)
    values = node.values
    lineno = node.lineno
    bc = ctx.bc

    def has_ext_syntax():
        return not all(keys)

    def is_create_dict():
        return expr_ctx_ty is ast.Load

    if has_ext_syntax():
        if is_create_dict():
            # use ext syntax create dict.
            def process_group():  # build dict
                nonlocal count
                if group:
                    count += 1
                    for k, v in group:
                        py_emit(k, ctx)
                        py_emit(v, ctx)
                    bc.append(BUILD_MAP(len(group), lineno=lineno))
                    group.clear()

            count = 0
            group = []
            for key, value in zip(keys, values):
                if key is None:
                    process_group()
                    py_emit(value, ctx)  # unpack bundle value.
                    count += 1
                else:
                    group.append((key, value))
            process_group()
            bc.append(BUILD_MAP_UNPACK(count, lineno=lineno))

        else:
            # use ext syntax destructuring dict.
            def dict_packing_exc():
                exc = SyntaxError()
                exc.lineno = lineno
                exc.msg = "dict packing must occur in the last position of dict literal."
                return exc

            if keys[-1] is not None:
                raise dict_packing_exc()

            pack = values[-1]
            bc.extend([
                LOAD_ATTR('copy', lineno=lineno),
                CALL_FUNCTION(0),
                DUP_TOP(),
                LOAD_ATTR('pop'),
                *duplicate_top_one(len(keys) - 2),  # prepare dup top.
            ])
            # gen destructuring value.
            for key, value in zip(keys[:-1], values[:-1]):
                if key is None:
                    raise dict_packing_exc()
                py_emit(key, ctx)
                bc.append(CALL_FUNCTION(1))
                py_emit(value, ctx)
            # generate **kw value.
            py_emit(pack, ctx)

    else:
        # create dict with origin syntax
        if is_create_dict():
            for key, value in zip(keys, values):
                py_emit(key, ctx)
                py_emit(value, ctx)
            bc.append(BUILD_MAP(len(keys), lineno=lineno))
            return

        # destructuring dict with origin syntax
        if not has_ext_syntax():
            bc.append(LOAD_ATTR('get', lineno=lineno))
            # dup top before gen k,v code.
            bc.extend(duplicate_top_one(len(keys) - 1))
            # dict -> get value and store.
            for key, value in zip(keys, values):
                py_emit(key, ctx)
                bc.append(CALL_FUNCTION(1))
                py_emit(value, ctx)


@py_emit.case(ast.Subscript)
def py_emit(node: ast.Subscript, ctx: Context):
    """
    title: subscript
    test:

    >>> x = {1: 2, (3,  4): 10}
    >>> assert x[1] == 2
    >>> assert  x[3, 4] == 10
    >>> del x[1]
    >>> del x[3, 4]
    >>> assert not x
    >>> x = [1, 2, 3]
    >>> x[:2] = [2, 3]
    >>> assert x[:2] == [2, 3]
    >>> x[:] = []
    >>> assert not x
    >>> x.append(1)
    >>> x += [2, 3, 4]
    >>> del x[:2]
    >>> assert len(x) = 2
    >>> class S:
    >>>     def __getitem__(self, i):
    >>>        if i == (slice(1, 2, None), slice(2, 3, -1)):
    >>>             return 42
    >>>        raise ValueError
    >>> assert S()[1:2, 2:3:-1] == 42

    """
    expr_context_ty = type(node.ctx)
    py_emit(node.value, ctx)

    if sys.version_info >= (3, 8):
        # See https://github.com/python/cpython/pull/9605
        py_emit(node.slice, ctx)
    else:
        py_emit(node.slice.value, ctx)

    command = {
        ast.Del: DELETE_SUBSCR,
        ast.Store: STORE_SUBSCR,
        ast.Load: BINARY_SUBSCR,
    }.get(expr_context_ty)

    ctx.bc.append(command(lineno=node.lineno))


@py_emit.case(ast.Name)
def py_emit(node: ast.Name, ctx: Context):
    command = {
        ast.Load: ctx.load_name,
        ast.Store: ctx.store_name,
        ast.Del: ctx.del_name,
    }.get(type(node.ctx))

    assert command is not None

    command(
        node.id,
        lineno=node.lineno,
    )


@py_emit.case(ast.Attribute)
def py_emit(node: ast.Attribute, ctx: Context):
    """
    title: attribute
    prepare:
    >>> class S: pass
    >>> s = S()

    test:
    >>> s.x = 1
    >>> assert s.x == 1
    >>> del s.x
    >>> assert not hasattr(s, 'x')
    """
    py_emit(node.value, ctx)

    command = {
        ast.Store: STORE_ATTR,
        ast.Load: LOAD_ATTR,
        ast.Del: DELETE_ATTR,
    }.get(type(node.ctx))

    assert command is not None
    ctx.bc.append(
        command(
            node.attr,
            lineno=node.lineno,
        ),
    )
