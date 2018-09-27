from kizmi.extended_python.parser import parse
print(
    parse(r"""
from kizmi.expr_first_lang.parser import parse
from kizmi.expr_first_lang.parser import parse
print(
    parse(r'''

''').result)
    
""").result)
