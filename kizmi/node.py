import typing as t
from collections import defaultdict

from kizmi.utils import partition


def _strict_force(it):
    if isinstance(it, PendingNode):
        return it.getter()
    return it


class Node:
    def mutate(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    @staticmethod
    def map(f, context, node: 'Node'):
        def apply(ctx, subpattern: Node):
            ctx, value = f(ctx, subpattern)
            return visit(ctx, value)

        def visit(ctx, subpattern: Node):
            if isinstance(subpattern, (TextNode, PendingNode, AttributeNode)):
                return subpattern
            elif isinstance(subpattern, TagNode):
                new = TagNode()
                children = []
                for each in subpattern.children:
                    ctx, value = apply(ctx, each)
                    children.append(value)
                new.name = subpattern.name
                return new
            raise TypeError

        return apply(context, node)

    @staticmethod
    def map_df(f, context, node: 'Node'):
        def apply(ctx, subpattern: Node):
            ctx, value = visit(ctx, subpattern)
            return f(ctx, value)

        def visit(ctx, subpattern: Node):
            if isinstance(subpattern, (TextNode, PendingNode, AttributeNode)):
                return subpattern
            if isinstance(subpattern, TagNode):
                new = TagNode()
                children = []
                for each in subpattern.children:
                    ctx, value = apply(ctx, each)
                    children.append(value)
                new.name = subpattern.name
                return new
            raise TypeError

        return apply(context, node)

    def dump(self, path, indent_white='    '):
        text = self.dumps(indent_white)
        with open(path, 'w', encoding='utf8') as fw:
            fw.write(text)

    def dumps(self, indent_white='    '):
        space_cat = ' '.join

        def dump_imp(indent_level, node: Node):

            if isinstance(node, TextNode):
                return indent_white * indent_level + node.value

            if isinstance(node, PendingNode):
                return dump_imp(indent_level, node.getter())

            if isinstance(node, AttributeNode):
                key, values = node.key, node.values
                # print(key,  values.__class__, values)
                value = space_cat(values).replace('"', '\\"')
                return f'{key}="{value}"' if values else key

            if isinstance(node, TagNode):
                children = [_strict_force(each) for each in node.children]

                attrs, non_attrs = partition(
                    children, lambda it: isinstance(it, AttributeNode))

                attr_info = space_cat(
                    dump_imp(indent_level, attr)
                    for attr in AttributeNode.merge(*attrs))

                if attr_info:
                    attr_info = ' ' + attr_info
                name = node.name
                indent = indent_white * indent_level
                if non_attrs:
                    content = '\n'.join(
                        dump_imp(indent_level + 1, non_attr)
                        for non_attr in non_attrs)
                    return f'{indent}<{name}{attr_info}>\n{content}\n{indent}</{name}>'
                else:
                    return f'{indent}<{name}{attr_info}/>'
            raise TypeError

        return dump_imp(0, self)


class TextNode(Node):
    value: str


class PendingNode(Node):
    getter: t.Callable[[], Node]


class AttributeNode(Node):
    key: str
    values: t.List[str]

    @staticmethod
    def merge(*attrs: 'AttributeNode'):
        look_up = defaultdict(list)
        for each in attrs:
            look_up[each.key].extend(each.values)

        for k, v in look_up.items():
            attr = AttributeNode()
            attr.key = k
            attr.values = v
            yield attr


class TagNode(Node):
    name: str
    children: t.List[Node]

    def add_child(self, node: Node):
        self.children.append(node)
