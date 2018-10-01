from .dbg_ast import *
from string import Template
from textwrap import dedent, indent
from yapf.yapflib.yapf_api import FormatCode
import typing as t

_Code = t.List[t.Union[str, '_Code', t.Callable[[], '_Code']]]
T = t.TypeVar('T')


def dumps(codes: _Code, indent=''):
    if callable(codes):
        return dumps(codes(), indent)
    if isinstance(codes, str):
        return indent + codes
    if isinstance(codes, list):
        return f'\n'.join(map(lambda it: dumps(it, indent + '    '), codes))
    raise TypeError


class Proc:
    codes: _Code

    def __init__(self, codes: _Code):
        self.codes = codes

    def __add__(self, other: 'Proc'):
        return Proc([*self.codes, other])

    def __xor__(self, other):
        return Proc([*self.codes, *other])

    def __str__(self):
        return dumps(self.codes)


class RichList(t.List[T]):
    def any(self, predicate=None):
        if predicate is None:
            return any(self)
        return any(map(predicate, self))

    def find_all(self, predicate):
        return RichList(each for each in self if predicate(each))


class Context:
    current_table: str
    tables: RichList[Table]
    relations: RichList[Relation]

    def __init__(self, current_table: str, tables, relations):
        self.current_table = current_table
        self.tables = tables
        self.relations = relations

    def update(self, current_table=None, tables=None, relations=None):
        return Context(current_table or self.current_table, tables
                       or self.tables, relations or self.relations)

    def visit(self, node, proc):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method)
        return visitor(node, proc)

    def visit_Table(self, node, proc: Proc):
        table_name = node.name
        proc += f'class {table_name}(__base__):'

        proc += [
            f'__tablename__ = {table_name.lower()!r}',
            "# primary keys",
        ]

        proc_ = Proc([])
        self = self.update(current_table=table_name)

        ## primary key
        proc_, ctx = self.visit(node.primary, proc_)

        ## fields
        proc_ += '# fields'

        proc_ += 'dbg_is_status_activated = db.Column(db.Boolean, nullable=False, default=True)'

        constructor_default_args = []
        constructor_mandatory_args = []

        for each in node.fields:
            proc_, ctx = ctx.visit(each, proc_)
            if each.default:
                constructor_default_args.append(
                    f'{each.name} : {each.type.v} = {each.default.v}')
            else:
                constructor_mandatory_args.append(f'{each.name} : {each.type.v}')

        proc_ += '# constructor'
        proc_ ^= [
            'def __init__(self, *, {}):'.format(
                ','.join(constructor_mandatory_args + constructor_default_args)),
            [
                'super().__init__({})'.format(', '.join(
                    f'{each.name}={each.name}' for each in node.fields))
            ]
        ]

        ## repr
        proc_ += '# repr'
        proc_ += 'def __repr__(self):'
        fields = []
        for each in node.reprs or (node.primary.name, *(each.name
                                                        for each in node.fields)):
            fields.append(
                Template('$field = {self.$field}').substitute(field=each))
        proc_ += [
            Template('return f"$tb($fields)"').substitute(
                tb=table_name, fields=', '.join(fields))
        ]

        ## relationships
        @ctx.relations.find_all
        def all_rels(rel: Relation):
            return rel.right == table_name or rel.left == table_name

        all_rels: t.List[Relation]
        if any(all_rels):
            proc_ += '# relationship'

        for rel in all_rels:
            rel_name = f'{rel.left}{rel.right}'
            self, other = rel.left, rel.right
            if rel.right == table_name:
                self, other = other, self
            proc_ += '@builtins.property'
            proc_ += f'def rel_{other.lower()}(self) -> "db.Query[{rel_name}]":'
            proc_ += [
                f'return db.filter_from_table({rel_name}, {rel_name}.{self.lower()}_id == self.id)'
            ]

        # proc_ += '# auto delete'
        # proc_ += 'def delete(self) -> int:'
        # proc_ += ['ret = 0']
        # const_decided_deleted = 0
        # for rel in all_rels:
        #     rel_name = f'{rel.left}{rel.right}'
        #     self, other = rel.left, rel.right
        #     weight = rel.weight
        #     if rel.right == table_name:
        #         self, other = other, self
        #         weight = tuple(reversed(weight))
        #     self_w, other_w = weight
        #     if not self_w:
        #         # 一对一
        #         proc += [f'__session__.delete(self.rel_{other.lower()})']
        #         const_decided_deleted += 1
        #     elif other_w:
        #         # 多对多
        #         proc += [
        #             f'rel = self.rel_{other.lower()}'
        #             f'rev_rels = rel.{self.lower()}.all()',
        #         ]
        #         proc += [
        #             f'if len(rev_rels) is 1 and rev_rels[0] == self:',
        #             [
        #                 f'for each in rel.{other.lower()}.all():',
        #                 [f'__session__.delete(each)', 'ret += 1'],
        #                 '__session__.delete(rel)'
        #             ],
        #         ]
        #     else:
        #         # 多对一
        #         proc += [f'self.rel_{other.lower()}.{self.lower()}.delete()']

        proc += proc_.codes
        return proc, ctx


    def _visit_field(self, node: t.Union[Field, Primary], proc: Proc):
        kws = []

        if '~' in node.option:
            seq_name = f'{self.current_table.lower()}_id_seq'
            kws.append(f'db.Sequence({seq_name!r})')

        if isinstance(node, Primary):
            kws.append('primary_key=True, autoincrement=True')

        if '?' in node.option:
            kws.append('nullable=True')
        else:
            kws.append('nullable=False')

        if '!' in node.option:
            kws.append('unique=True')

        kwargs = ', '.join(kws)
        proc += f'{node.name} = db.Column({node.type.v}, {kwargs})'
        return proc, self

    def visit_Field(self, node, proc):
        return self._visit_field(node, proc)

    def visit_Primary(self, node, proc):
        return self._visit_field(node, proc)


    def visit_Relation(self, node: Relation, proc: Proc):
        rel_name = f'{node.left}{node.right}'
        proc += f'class {rel_name}(__base__):'

        proc += [
            f'__tablename__ = {rel_name.lower()!r}',
            '# primary keys',
            f'{node.left.lower()}_id = db.Column(db.Integer, primary_key=True)',
            f'{node.right.lower()}_id = db.Column(db.Integer, primary_key=True)',
        ]

        proc_ = Proc([])

        ctx = self.update(current_table=rel_name)
        proc_ += '# fields'
        proc_ += 'dbg_is_status_activated = db.Column(db.Boolean, nullable=False, default=True)'

        constructor_default_args = []
        constructor_mandatory_args = []

        for each in node.fields:
            proc_, ctx = ctx.visit(each, proc_)
            if each.default:
                constructor_default_args.append(
                    f'{each.name} : {each.type.v} = {each.default.v}')
            else:
                constructor_mandatory_args.append(f'{each.name} : {each.type.v}')

        proc_ += '# constructor'
        proc_ ^= [
            'def __init__(self, *, {}):'.format(
                ','.join(constructor_mandatory_args + constructor_default_args)),
            [
                'super().__init__({})'.format(', '.join(
                    f'{each.name}={each.name}' for each in node.fields))
            ]
        ]

        proc_ += '# relationship'

        def add_rel(rel_to: str):
            return [
                '@builtins.property',
                f'def {rel_to.lower()}(self) -> "db.typing.Optional[{rel_to}]":',
                [
                    f'return db.filter_from_table({rel_to}, {rel_to}.id == self.{rel_to.lower()}_id).first()'
                ]
            ]

        proc_ ^= add_rel(node.left)
        proc_ ^= add_rel(node.right)

        proc_ += '# repr'
        proc_ += 'def __repr__(self):'

        fields = []

        for each in (f'{node.left.lower()}_id', f'{node.right.lower()}_id',
                     *[each.name for each in node.fields]):
            fields.append(
                Template('$field = {self.$field}').substitute(field=each))
        proc_ += [
            Template('return f"$rel($fields)"').substitute(
                rel=rel_name, fields=', '.join(fields))
        ]

        proc += proc_.codes
        return proc, ctx


    def visit_Engine(self, node: Engine, proc: Proc):
        configs = {**node.configs}
        url = configs['url']
        del configs['url']
        proc += 'engine = db.create_engine({url}, convert_unicode=True, {ops})'.format(
            url=url, ops=', '.join(f"{k} = {v}" for k, v in configs.items()))
        proc += '__session__ = db.scoped_session(db.sessionmaker(autocommit=False, autoflush=False, bind=engine))'
        proc ^= [
            '__base__ = db.declarative_base()',
            '__base__.query = __session__.query_property()'
        ]
        return proc, self

    def visit_Python(self, node: Python, proc: Proc):
        proc += indent(dedent(node.codes), '    ')
        proc += '\n'
        return proc, self


def code_gen(asts: list):
    relations = RichList()
    tables = RichList()
    for each in asts:
        if isinstance(each, Relation):
            relations.append(each)
        elif isinstance(each, Table):
            tables.append(each)
        elif isinstance(each, (Python, Engine)):
            pass
        else:
            raise TypeError(type(each))

    ctx = Context('', tables, relations)
    proc = Proc([
        'from kizmi.database.types import *',
        'import kizmi.database.infrastructure as db',
        'import builtins',
    ])
    for each in asts:
        proc, ctx = ctx.visit(each, proc)
    proc += '__base__.metadata.create_all(bind=engine)'
    proc += 'session = __session__'
    return FormatCode(dedent(dumps(proc.codes)))[0]
