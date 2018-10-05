from yapypy.extended_python.emit_impl import *

_non_ctx: Context = None


def py_compile(node, filename='<unknown>'):
    if isinstance(node, Tag):
        ctx = Context(
            Bytecode(),
            IndexedAnalyzedSymTable.from_raw(node.tag),
            _non_ctx,
            [],
        )

        try:
            py_emit(node.it, ctx)
        except SyntaxError as exc:
            exc.filename = filename
            raise exc

        return ctx.bc.to_code()
    else:
        tag = to_tagged_ast(node)
        return py_compile(tag)
