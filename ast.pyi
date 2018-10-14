import typing, abc
NoneType = None


class AST(abc.ABC):
    def __init__(self, *args, lineno: int = None, colno: int = None, **kwargs):
        pass


class alias(AST):
    asname: typing.Union[str, NoneType]
    name: typing.Union[str]


class Import(AST):
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    names: typing.List[typing.Union[typing.Union[alias]]]


class ImportFrom(AST):
    lineno: typing.Union[int]
    level: typing.Union[int]
    col_offset: typing.Union[int]
    module: typing.Union[str, NoneType]
    names: typing.List[typing.Union[typing.Union[alias]]]


class Store(AST):
    pass


class Name(AST):
    ctx: typing.Union[Del, Load, Store]
    id: typing.Union[str]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Str(AST):
    s: typing.Union[str]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Load(AST):
    pass


class List(AST):
    elts: typing.List[typing.Union[
        typing.Union[Name, Str, Subscript, BinOp, Attribute]]]
    ctx: typing.Union[Load]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Assign(AST):
    value: typing.Union[Name, Str, Tuple, ListComp, Lambda, NameConstant,
                        JoinedStr, Compare, Num, List, BoolOp, IfExp,
                        Subscript, UnaryOp, Call, Dict, BinOp, Attribute,
                        DictComp]
    targets: typing.List[typing.Union[
        typing.Union[Tuple, Subscript, Attribute, Name]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class arg(AST):
    annotation: typing.Union[Name, Str, Subscript, NoneType, Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    arg: typing.Union[str]


class arguments(AST):
    defaults: typing.List[typing.Union[
        typing.Union[Tuple, Str, Name, Lambda, NameConstant, List, Attribute]]]
    kwonlyargs: typing.List[typing.Union[typing.Union[arg]]]
    kw_defaults: typing.List[typing.Union[typing.Union[NameConstant]]]
    vararg: typing.Union[arg, NoneType]
    kwarg: typing.Union[arg, NoneType]
    args: typing.List[typing.Union[typing.Union[arg]]]


class Expr(AST):
    value: typing.Union[YieldFrom, Str, Yield, Call]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Attribute(AST):
    value: typing.Union[Name, Str, Subscript, Call, Attribute]
    ctx: typing.Union[Load, Store]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    attr: typing.Union[str]


class Call(AST):
    args: typing.List[typing.Union[typing.Union[
        Name, Str, Tuple, ListComp, Starred, Dict, Lambda, NameConstant,
        JoinedStr, IfExp, Num, List, BoolOp, UnaryOp, Subscript, Call,
        GeneratorExp, BinOp, Attribute, DictComp]]]
    func: typing.Union[Name, Subscript, Call, Attribute]
    keywords: typing.List[typing.Union[typing.Union[keyword]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class IfExp(AST):
    orelse: typing.Union[Tuple, Str, Name, Lambda, Compare, Num, List, Call,
                         Dict, Attribute]
    test: typing.Union[Name, Compare, BoolOp, Call, Attribute]
    body: typing.Union[Name, Call, Compare, Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Return(AST):
    value: typing.Union[Name, Str, NoneType, ListComp, Tuple, Lambda,
                        NameConstant, IfExp, Compare, JoinedStr, List, BoolOp,
                        Subscript, UnaryOp, Call, Dict, BinOp, Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class FunctionDef(AST):
    body: typing.List[typing.Union[
        typing.Union[AugAssign, For, Import, AnnAssign, FunctionDef, ClassDef,
                     While, Return, If, ImportFrom, Nonlocal, Pass, Try,
                     Assert, Delete, With, Expr, Raise, Assign]]]
    returns: typing.Union[Name, Str, NameConstant, Subscript, NoneType,
                          Attribute]
    lineno: typing.Union[int]
    decorator_list: typing.List[typing.Union[typing.
                                             Union[Attribute, Name, Call]]]
    col_offset: typing.Union[int]
    args: typing.Union[arguments]
    name: typing.Union[str]


class Dict(AST):
    values: typing.List[typing.Union[
        typing.Union[Name, Str, ListComp, NameConstant, List, BoolOp, Call,
                     BinOp, Attribute]]]
    keys: typing.List[typing.Union[typing.Union[Str, NameConstant, NoneType]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Tuple(AST):
    elts: typing.List[
        typing.Union[Name, Str, Tuple, Starred, NameConstant, Num, List,
                     Ellipsis, BoolOp, Subscript, Call, BinOp, Attribute]]
    ctx: typing.Union[Load, Store]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class comprehension(AST):
    target: typing.Union[Tuple, Name]
    iter: typing.Union[Name, Call, Attribute, List]
    ifs: typing.List[typing.Union[typing.Union[BoolOp, Name, Compare, Call]]]
    is_async: typing.Union[int]


class DictComp(AST):
    value: typing.Union[Name, Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    generators: typing.List[comprehension]
    key: typing.Union[Name]


class For(AST):
    target: typing.Union[Name, Tuple, Attribute]
    body: typing.List[typing.Union[
        typing.Union[AugAssign, For, Return, If, Try, Expr, Assign]]]
    iter: typing.Union[Attribute, Name, Tuple, Call]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Or(AST):
    pass


class Not(AST):
    pass


class UnaryOp(AST):
    operand: typing.Union[Name, Num, BoolOp, Subscript, Call, Attribute]
    lineno: typing.Union[int]
    op: typing.Union[USub, Not]
    col_offset: typing.Union[int]


class UnaryOpC(AST):
    operand: typing.Union[Name, Num, BoolOp, Subscript, Call, Attribute]
    lineno: typing.Union[int]
    op: typing.Union[USub, Not]
    col_offset: typing.Union[int]


class BoolOp(AST):
    values: typing.List[typing.Union[
        typing.Union[Name, Str, Tuple, Compare, IfExp, List, BoolOp, UnaryOp,
                     Subscript, Call, Dict, Attribute]]]
    op: typing.Union[Or, And]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class FormattedValue(AST):
    value: typing.Union[Attribute, Name, Call]
    conversion: typing.Union[int]
    format_spec: typing.Union[NoneType]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class JoinedStr(AST):
    values: typing.List[typing.Union[typing.Union[Str, FormattedValue]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class If(AST):
    body: typing.List[typing.Union[typing.Union[
        Break, For, AugAssign, Expr, AnnAssign, FunctionDef, ClassDef, Return,
        If, ImportFrom, Try, Assert, Pass, Continue, With, Raise, Assign]]]
    orelse: typing.List[typing.Union[
        typing.Union[AugAssign, AnnAssign, FunctionDef, Return, If, ImportFrom,
                     Try, With, Continue, Expr, Raise, Assign]]]
    test: typing.Union[Name, Compare, BoolOp, UnaryOp, Subscript, Call,
                       Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class YieldFrom(AST):
    value: typing.Union[Attribute, Name, Tuple, Call]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Is(AST):
    pass


class Ellipsis(AST):
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Compare(AST):
    ops: typing.List[typing.Union[
        typing.Union[NotIn, IsNot, Gt, GtE, Lt, Eq, Is, In, LtE, NotEq]]]
    comparators: typing.List[typing.Union[
        typing.Union[Tuple, Str, Name, NameConstant, Num, Ellipsis, UnaryOp,
                     Subscript, Call, GeneratorExp, Attribute]]]
    left: typing.Union[Name, Str, NameConstant, Subscript, Call, BinOp,
                       Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class NameConstant(AST):
    value: typing.Union[bool, NoneType]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class AnnAssign(AST):
    target: typing.Union[Name, Attribute]
    value: typing.Union[Name, NameConstant, IfExp, Subscript, Call, NoneType,
                        BinOp, Attribute]
    annotation: typing.Union[Attribute, Name, Subscript, Str]
    simple: typing.Union[int]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Raise(AST):
    exc: typing.Union[Attribute, Name, Call, NoneType]
    cause: typing.Union[Name, NoneType]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Num(AST):
    n: typing.Union[int]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Index(AST):
    value: typing.Union[Name, Str, Tuple, NameConstant, Num, BoolOp, Subscript,
                        UnaryOp, Call, BinOp, Attribute]


class Subscript(AST):
    value: typing.Union[Attribute, Name, Call]
    ctx: typing.Union[Del, Load, Store]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    slice: typing.Union[Slice, Index]


class keyword(AST):
    value: typing.Union[Name, Str, Tuple, NameConstant, Num, List, BoolOp,
                        Subscript, Call, BinOp, Attribute]
    arg: typing.Union[str, NoneType]


class ClassDef(AST):
    body: typing.List[typing.Union[typing.Union[
        AnnAssign, FunctionDef, ClassDef, Delete, Pass, Expr, Assign]]]
    name: typing.Union[str]
    bases: typing.List[typing.Union[typing.
                                    Union[Attribute, Name, Subscript, Call]]]
    keywords: typing.List[typing.Union[typing.Union[keyword]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    decorator_list: typing.List[typing.Union[typing.Union[Name]]]


class Pass(AST):
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class ExceptHandler(AST):
    body: typing.List[typing.Union[
        typing.Union[Import, FunctionDef, ClassDef, Return, If, ImportFrom,
                     Pass, Continue, Expr, Raise, Assign]]]
    name: typing.Union[str, NoneType]
    type: typing.Union[Tuple, Name, NoneType]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Try(AST):
    body: typing.List[typing.Union[
        typing.Union[For, AugAssign, Import, FunctionDef, Return, If,
                     ImportFrom, Try, With, Expr, Assign]]]
    finalbody: typing.List[typing.Union[typing.
                                        Union[Expr, Assert, Assign, If]]]
    handlers: typing.List[typing.Union[typing.Union[ExceptHandler]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Gt(AST):
    pass


class NotEq(AST):
    pass


class Module(AST):
    body: typing.List[typing.Union[
        typing.Union[Import, FunctionDef, ClassDef, If, ImportFrom, Try,
                     Delete, Expr, Assign]]]


class And(AST):
    pass


class Eq(AST):
    pass


class Lambda(AST):
    body: typing.Union[Name, NameConstant, Compare, Call]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    args: typing.Union[arguments]


class Starred(AST):
    value: typing.Union[Name, Subscript, Call, GeneratorExp, Attribute]
    ctx: typing.Union[Load, Store]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class While(AST):
    test: typing.Union[Name, Compare, Num, Call, Attribute]
    body: typing.List[typing.Union[typing.Union[Pass, Expr, If, Assign]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Break(AST):
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Add(AST):
    pass


class BinOp(AST):
    right: typing.Union[Name, Str, Tuple, Num, List, BoolOp, Subscript, Call,
                        Dict, BinOp, Attribute]
    left: typing.Union[Tuple, Str, Name, ListComp, Num, List, Subscript, Call,
                       BinOp, Attribute]
    op: typing.Union[Add, BitAnd, Sub, FloorDiv, BitXor, Mult, Mod]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class ListComp(AST):
    elt: typing.Union[Name, Subscript, Call, Attribute]
    generators: typing.List[typing.Union[typing.Union[comprehension]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class withitem(AST):
    optional_vars: typing.Union[Name, NoneType]
    context_expr: typing.Union[Attribute, Name, Call]


class With(AST):
    body: typing.List[typing.Union[
        typing.Union[For, Return, If, ImportFrom, Try, Expr, Raise, Assign]]]
    items: typing.List[typing.Union[typing.Union[withitem]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Yield(AST):
    value: typing.Union[Name, Tuple, NameConstant, Subscript, Call, BinOp,
                        Attribute]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Nonlocal(AST):
    names: typing.List[typing.Union[typing.Union[str]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class AugAssign(AST):
    target: typing.Union[Name, Subscript, Attribute]
    value: typing.Union[Name, Num, Call, BinOp, Attribute]
    op: typing.Union[BitOr, Sub, Add]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class GeneratorExp(AST):
    elt: typing.Union[Tuple, Name, IfExp, Compare, Subscript, Call, BinOp]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    generators: typing.List[typing.Union[typing.Union[comprehension]]]


class Continue(AST):
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class NotIn(AST):
    pass


class In(AST):
    pass


class IsNot(AST):
    pass


class FloorDiv(AST):
    pass


class Sub(AST):
    pass


class Slice(AST):
    lower: typing.Union[Name, Call, Num, NoneType]
    step: typing.Union[UnaryOp, NoneType]
    upper: typing.Union[UnaryOp, Num, NoneType]


class BitOr(AST):
    pass


class USub(AST):
    pass


class BitXor(AST):
    pass


class Mult(AST):
    pass


class Lt(AST):
    pass


class Del(AST):
    pass


class Delete(AST):
    targets: typing.List[typing.Union[typing.Union[Name, Subscript]]]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]


class Mod(AST):
    pass


class Assert(AST):
    msg: typing.Union[Str, BinOp, NoneType]
    lineno: typing.Union[int]
    col_offset: typing.Union[int]
    test: typing.Union[Compare, Call]


class GtE(AST):
    pass


class LtE(AST):
    pass


class BitAnd(AST):
    pass


"""
    ast
    ~~~

    The `ast` module helps Python applications to process trees of the Python
    abstract syntax grammar.  The abstract syntax itself might change with
    each Python release; this module helps to find out programmatically what
    the current grammar looks like and allows modifications of it.

    An abstract syntax tree can be generated by passing `ast.PyCF_ONLY_AST` as
    a flag to the `compile()` builtin function or by using the `parse()`
    function from this module.  The result will be a tree of objects whose
    classes all inherit from `ast.AST`.

    A modified abstract syntax tree can be compiled into a Python code object
    using the built-in `compile()` function.

    Additionally various helper functions are provided that make working with
    the trees simpler.  The main intention of the helper functions and this
    module in general is to provide an easy to use interface for libraries
    that work tightly with the python syntax (template engines for example).


    :copyright: Copyright 2008 by Armin Ronacher.
    :license: Python License.
"""
from _ast import *


def parse(source, filename='<unknown>', mode='exec'):
    """
    Parse the source into an AST node.
    Equivalent to compile(source, filename, mode, PyCF_ONLY_AST).
    """
    return compile(source, filename, mode, PyCF_ONLY_AST)


_NUM_TYPES = (int, float, complex)


def literal_eval(node_or_string):
    """
    Safely evaluate an expression node or a string containing a Python
    expression.  The string or node provided may only consist of the following
    Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
    sets, booleans, and None.
    """
    if isinstance(node_or_string, str):
        node_or_string = parse(node_or_string, mode='eval')
    if isinstance(node_or_string, Expression):
        node_or_string = node_or_string.body

    def _convert(node):
        if isinstance(node, Constant):
            return node.value
        elif isinstance(node, (Str, Bytes)):
            return node.s
        elif isinstance(node, Num):
            return node.n
        elif isinstance(node, Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, List):
            return list(map(_convert, node.elts))
        elif isinstance(node, Set):
            return set(map(_convert, node.elts))
        elif isinstance(node, Dict):
            return dict((_convert(k), _convert(v))
                        for k, v in zip(node.keys, node.values))
        elif isinstance(node, NameConstant):
            return node.value
        elif isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
            operand = _convert(node.operand)
            if isinstance(operand, _NUM_TYPES):
                if isinstance(node.op, UAdd):
                    return +operand
                else:
                    return -operand
        elif isinstance(node, BinOp) and isinstance(node.op, (Add, Sub)):
            left = _convert(node.left)
            right = _convert(node.right)
            if isinstance(left, _NUM_TYPES) and isinstance(right, _NUM_TYPES):
                if isinstance(node.op, Add):
                    return left + right
                else:
                    return left - right
        raise ValueError('malformed node or string: ' + repr(node))

    return _convert(node_or_string)


def dump(node, annotate_fields=True, include_attributes=False):
    """
    Return a formatted dump of the tree in *node*.  This is mainly useful for
    debugging purposes.  The returned string will show the names and the values
    for fields.  This makes the code impossible to evaluate, so if evaluation is
    wanted *annotate_fields* must be set to False.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.
    """

    def _format(node):
        if isinstance(node, AST):
            fields = [(a, _format(b)) for a, b in iter_fields(node)]
            rv = '%s(%s' % (node.__class__.__name__, ', '.join(
                ('%s=%s' % field for field in fields) if annotate_fields else
                (b for a, b in fields)))
            if include_attributes and node._attributes:
                rv += fields and ', ' or ' '
                rv += ', '.join('%s=%s' % (a, _format(getattr(node, a)))
                                for a in node._attributes)
            return rv + ')'
        elif isinstance(node, list):
            return '[%s]' % ', '.join(_format(x) for x in node)
        return repr(node)

    if not isinstance(node, AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)


def copy_location(new_node, old_node):
    """
    Copy source location (`lineno` and `col_offset` attributes) from
    *old_node* to *new_node* if possible, and return *new_node*.
    """
    for attr in 'lineno', 'col_offset':
        if attr in old_node._attributes and attr in new_node._attributes \
           and hasattr(old_node, attr):
            setattr(new_node, attr, getattr(old_node, attr))
    return new_node


def fix_missing_locations(node):
    """
    When you compile a node tree with compile(), the compiler expects lineno and
    col_offset attributes for every node that supports them.  This is rather
    tedious to fill in for generated nodes, so this helper adds these attributes
    recursively where not already set, by setting them to the values of the
    parent node.  It works recursively starting at *node*.
    """

    def _fix(node, lineno, col_offset):
        if 'lineno' in node._attributes:
            if not hasattr(node, 'lineno'):
                node.lineno = lineno
            else:
                lineno = node.lineno
        if 'col_offset' in node._attributes:
            if not hasattr(node, 'col_offset'):
                node.col_offset = col_offset
            else:
                col_offset = node.col_offset
        for child in iter_child_nodes(node):
            _fix(child, lineno, col_offset)

    _fix(node, 1, 0)
    return node


def increment_lineno(node, n=1):
    """
    Increment the line number of each node in the tree starting at *node* by *n*.
    This is useful to "move code" to a different location in a file.
    """
    for child in walk(node):
        if 'lineno' in child._attributes:
            child.lineno = getattr(child, 'lineno', 0) + n
    return node


def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass


def iter_child_nodes(node):
    """
    Yield all direct child nodes of *node*, that is, all fields that are nodes
    and all items of fields that are lists of nodes.
    """
    for name, field in iter_fields(node):
        if isinstance(field, AST):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, AST):
                    yield item


def get_docstring(node, clean=True):
    """
    Return the docstring for the given node or None if no docstring can
    be found.  If the node provided does not have docstrings a TypeError
    will be raised.
    """
    if not isinstance(node, (AsyncFunctionDef, FunctionDef, ClassDef, Module)):
        raise TypeError("%r can't have docstrings" % node.__class__.__name__)
    if not (node.body and isinstance(node.body[0], Expr)):
        return
    node = node.body[0].value
    if isinstance(node, Str):
        text = node.s
    elif isinstance(node, Constant) and isinstance(node.value, str):
        text = node.value
    else:
        return
    if clean:
        import inspect
        text = inspect.cleandoc(text)
    return text


def walk(node):
    """
    Recursively yield all descendant nodes in the tree starting at *node*
    (including *node* itself), in no specified order.  This is useful if you
    only want to modify nodes in place and don't care about the context.
    """
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(iter_child_nodes(node))
        yield node


class NodeVisitor(object):
    """
    A node visitor base class that walks the abstract syntax tree and calls a
    visitor function for every node found.  This function may return a value
    which is forwarded by the `visit` method.

    This class is meant to be subclassed, with the subclass adding visitor
    methods.

    Per default the visitor functions for the nodes are ``'visit_'`` +
    class name of the node.  So a `TryFinally` node visit function would
    be `visit_TryFinally`.  This behavior can be changed by overriding
    the `visit` method.  If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.

    Don't use the `NodeVisitor` if you want to apply changes to nodes during
    traversing.  For this a special visitor exists (`NodeTransformer`) that
    allows modifications.
    """

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item)
            elif isinstance(value, AST):
                self.visit(value)


class NodeTransformer(NodeVisitor):
    """
    A :class:`NodeVisitor` subclass that walks the abstract syntax tree and
    allows modification of nodes.

    The `NodeTransformer` will walk the AST and use the return value of the
    visitor methods to replace or remove the old node.  If the return value of
    the visitor method is ``None``, the node will be removed from its location,
    otherwise it is replaced with the return value.  The return value may be the
    original node in which case no replacement takes place.

    Here is an example transformer that rewrites all occurrences of name lookups
    (``foo``) to ``data['foo']``::

       class RewriteName(NodeTransformer):

           def visit_Name(self, node):
               return copy_location(Subscript(
                   value=Name(id='data', ctx=Load()),
                   slice=Index(value=Str(s=node.id)),
                   ctx=node.ctx
               ), node)

    Keep in mind that if the node you're operating on has child nodes you must
    either transform the child nodes yourself or call the :meth:`generic_visit`
    method for the node first.

    For nodes that were part of a collection of statements (that applies to all
    statement nodes), the visitor may also return a list of nodes rather than
    just a single node.

    Usually you use the transformer like this::

       node = YourTransformer().visit(node)
    """

    def generic_visit(self, node):
        for field, old_value in iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, AST):
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, AST):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, AST):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node
