import marshal
import os
import struct
import time
from importlib._bootstrap_external import MAGIC_NUMBER
from Redy.Tools.PathLib import Path
from rbnf.edsl.rbnf_analyze import check_parsing_complete
from wisepy.talking import Talking
from yapypy.extended_python import pycompat
from yapypy.extended_python.parser import parse as parse_ext_py
from yapypy.extended_python.py_compile import py_compile

python_ex = Talking()


def compile_ex_python_from_filename(filename, is_entry_point=True):
    with Path(filename).open('r') as fr:
        source_code = fr.read()
        result = parse_ext_py(source_code)
    result.state.filename = filename
    # double check parsed result.
    check_parsing_complete(source_code, result.tokens, result.state)
    ast = result.result
    code = py_compile(ast, filename, is_entrypoint=is_entry_point)
    return code


def compile_ex_python_from_source(source_code, is_entry_point=True):
    filename = '<unknown>'
    result = parse_ext_py(source_code)
    result.state.filename = filename
    check_parsing_complete(source_code, result.tokens, result.state)
    ast = result.result
    code = py_compile(ast, filename, is_entrypoint=is_entry_point)
    return code


@python_ex
def run(filename: str = None, c: str = None):
    """
    filename:  input filename
    c       :  input source code
    """
    if filename:
        code = compile_ex_python_from_filename(filename)
    elif c:
        code = compile_ex_python_from_source(c + '\n')
    else:
        raise ValueError
    exec(code, {})


@python_ex.alias('compile')
def _compile(*filenames: str):
    for filename in filenames:
        code = compile_ex_python_from_filename(filename)
        timestamp = struct.pack('i', int(time.time()))
        marshalled_code_object = marshal.dumps(code)
        filename, ext = os.path.splitext(filename)
        filename = filename + '.pyc'
        with Path(filename).open('wb') as f:
            f.write(MAGIC_NUMBER)
            f.write(timestamp)
            f.write(b'A\x00\x00\x00')
            f.write(marshalled_code_object)


def python_ex_cli():
    python_ex.on()
