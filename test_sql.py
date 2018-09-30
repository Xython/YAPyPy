from kizmi.database.dbg_grammar import *
from kizmi.database.dbg_emit import *
from rbnf.edsl.rbnf_analyze import check_parsing_complete

test_code = """
engine {
    url = "mysql+pymysql://root:12345@localhost/test?charset=utf8"
}

python
    print('start engine')


User(id: Integer~){
    a: Integer = (1 + 2),
    b: Integer = (2 + 3)
}

Card(id: Integer~){
    content: String(30)!
}

User^ with ^Card {
    content: String(30)
}

"""
res = parse(test_code)
check_parsing_complete(test_code, res.tokens, res.state)

with open('test_orm.py', 'w') as f:
    f.write(code_gen(res.result))

