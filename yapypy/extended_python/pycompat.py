import sys
import types
import dis
from importlib.machinery import ModuleSpec
from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile
from Redy.Tools.PathLib import Path
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from importlib.abc import MetaPathFinder
from astpretty import pprint

class YAPyPyFinder(MetaPathFinder):
    @classmethod
    def find_spec(cls, fullname: str, paths, target=None):
        return find_yapypy_module_spec(fullname)


class YAPyPyLoader:
    def __init__(self, mod_name, mod_path):
        self.mod_name = mod_name
        self.mod_path = mod_path

    def exec_module(self, module):
        path = self.mod_path
        setattr(module, '__path__', path)
        setattr(module, '__package__', self.mod_name)
        setattr(module, '__loader__', self)
        bc = module.__bytecode__
        dis.dis(bc)
        exec(bc, module.__dict__)

    def create_module(self, spec):
        bc: types.CodeType = spec.__bytecode__
        doc = None
        if len(bc.co_consts) and isinstance(bc.co_consts[0], str):
            doc = bc.co_consts[0]
        mod = types.ModuleType(self.mod_name, doc)
        mod.__bytecode__ = bc
        return mod


def find_yapypy_module_spec(names):
    paths = sys.path
    for prospective_path in paths:
        path_secs = (prospective_path, *names.split('.'))
        *init, end = path_secs
        directory = Path(*init)
        if not directory.is_dir():
            continue
        end = end + '.yapypy'
        for each in directory.list_dir():
            each = each.relative()
            if each.lower() == end:
                module_path = directory.into(each)
                return get_yapypy_module_spec_from_path(
                    names, str(module_path))


def get_yapypy_module_spec_from_path(names, module_path):
    with Path(module_path).open('r') as fr:
        spec = ModuleSpec(names, YAPyPyLoader(names, module_path))
        __source__ = fr.read()
        result = parse(__source__, module_path)
        check_parsing_complete(__source__, result.tokens, result.state)
        __bytecode__ = py_compile(
            result.result, filename=module_path, is_entrypoint=False)
        spec.__source__ = __source__
        spec.__bytecode__ = __bytecode__
        return spec


sys.meta_path.append(YAPyPyFinder)
