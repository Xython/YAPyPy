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
        idx for idx, each in enumerate(node.elts)
        if isinstance(each, ast.Starred)
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
        idx for idx, each in enumerate(node.elts)
        if isinstance(each, ast.Starred)
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
    elif expr_ctx is ast.Del:
        for each in node.elts:
            py_emit(each, ctx)
    else:
        for each in node.elts:
            py_emit(each, ctx)

        ctx.bc.append(BUILD_LIST(len(node.elts), lineno=node.lineno))


@py_emit.case(ex_ast.ExDict)
def py_emit(node: ex_ast.ExDict, ctx: Context):
    keys = node.keys
    expr_ctx_ty = type(node.ctx)
    values = node.values
    if any(each for each in keys if each is None):
        raise NotImplemented
    else:
        if expr_ctx_ty is ast.Load:
            for key, value in zip(keys, values):
                py_emit(key, ctx)
                py_emit(value, ctx)
            ctx.bc.append(Instr('BUILD_MAP', len(keys), lineno=node.lineno))
        else:
            pass


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
    }[expr_context_ty]

    ctx.bc.append(command(lineno=node.lineno, ), )


@py_emit.case(ast.Name)
def py_emit(node: ast.Name, ctx: Context):
    command = {
        ast.Load: ctx.load_name,
        ast.Store: ctx.store_name,
        ast.Del: ctx.del_name,
    }[type(node.ctx)]

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
    }[type(node.ctx)]

    assert command is not None

    ctx.bc.append(command(
        node.attr,
        lineno=node.lineno,
    ), )
