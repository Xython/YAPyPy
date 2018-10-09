import sys
import types
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec

from Redy.Tools.PathLib import Path
from rbnf.edsl.rbnf_analyze import check_parsing_complete

from yapypy.extended_python.parser import parse
from yapypy.extended_python.py_compile import py_compile

is_debug = False


class YAPyPyFinder(MetaPathFinder):

    @classmethod
    def find_spec(cls, fullname: str, paths, target=None):

        paths = paths if isinstance(
            paths, list) else [paths] if isinstance(paths, str) else sys.path

        if is_debug:
            print(f'Searching module {fullname} from {paths[:5]}...')
        return find_yapypy_module_spec(fullname, paths)


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
        if is_debug:
            print(f'found module {self.mod_name} at {self.mod_path}.')
        exec(bc, module.__dict__)

    def create_module(self, spec):
        bc: types.CodeType = spec.__bytecode__
        doc = None
        if len(bc.co_consts) and isinstance(bc.co_consts[0], str):
            doc = bc.co_consts[0]
        mod = types.ModuleType(self.mod_name, doc)
        mod.__bytecode__ = bc
        return mod


def find_yapypy_module_spec(names, paths):

    def try_find(prospective_path):
        path_secs = (prospective_path, *names.split('.'))
        *init, end = path_secs
        directory = Path(*init)
        if not directory.is_dir():
            return
        for each in directory.list_dir():
            each_path_str = each.relative()
            # print(each_path_str, end)
            if each_path_str == end + '.py':
                module_path = directory.into(each_path_str)
                yield get_yapypy_module_spec_from_path(names, str(module_path))

            elif each_path_str == end and each.is_dir() and '__init__.py' in each:
                yield from try_find(str(each))

    for each in paths:
        found = next(try_find(each), None)
        if found:
            return found


def get_yapypy_module_spec_from_path(names, module_path):
    with Path(module_path).open('r') as fr:
        spec = ModuleSpec(names, YAPyPyLoader(names, module_path))
        __source__ = fr.read()
        result = parse(__source__, module_path)
        # pprint(result.result)
        check_parsing_complete(__source__, result.tokens, result.state)
        __bytecode__ = py_compile(
            result.result, filename=module_path, is_entrypoint=False)
        spec.__source__ = __source__
        spec.__bytecode__ = __bytecode__
        return spec


sys.meta_path.insert(0, YAPyPyFinder)
