from yapypy.extended_python.emit_impl import *

_non_ctx: Context = Context.__new__(Context)


def py_compile(node, filename='<unknown>'):
    if isinstance(node, Tag):
        ctx = _non_ctx.enter_new(node.tag)
        ctx.bc.append(LOAD_GLOBAL('type'))
        ctx.bc.append(STORE_GLOBAL('.type'))
        try:
            py_emit(node.it, ctx)
        except SyntaxError as exc:
            exc.filename = filename
            raise exc

        return ctx.bc.to_code()
    else:
        tag = to_tagged_ast(node)
        return py_compile(tag)
