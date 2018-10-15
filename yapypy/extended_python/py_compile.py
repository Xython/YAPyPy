from yapypy.extended_python.emit_impl import *
from os.path import splitext
from Redy.Tools.PathLib import Path

_non_ctx: Context = Context.__new__(Context)


def py_compile(node, filename='<unknown>', is_entrypoint=False):
    if isinstance(node, Tag):
        ctx = _non_ctx.enter_new(node.tag)
        ctx.bc.filename = filename

        ctx.bc.name = '__main__' if is_entrypoint else splitext(
            Path(filename).relative())[0]

        ctx.bc.append(LOAD_GLOBAL('type'))
        ctx.bc.append(STORE_GLOBAL('.yapypy.type'))
        ctx.bc.append(LOAD_GLOBAL('locals'))
        ctx.bc.append(STORE_GLOBAL('.yapypy.locals'))

        try:
            py_emit(node.it, ctx)
        except SyntaxError as exc:
            exc.filename = filename
            raise exc
        return ctx.bc.to_code()
    else:
        tag = to_tagged_ast(node)
        return py_compile(tag, filename, is_entrypoint=is_entrypoint)
