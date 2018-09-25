from kizmi.utils import partition
import kizmi.node as node
import copy
import typing as t
import abc


class Com(abc.ABC):
    @abc.abstractmethod
    def lens(self, **kwargs):
        raise NotImplemented

    @abc.abstractmethod
    def to_node(self) -> node.Node:
        raise NotImplemented

    @classmethod
    @abc.abstractmethod
    def help(cls):
        return 'undocumented'


class Texture(Com):
    value: str

    def lens(self, value: t.Optional[str] = None):
        new = Texture()
        new.value = value if value is not None else self.value
        return new

    def to_node(self):
        return node.TextNode().mutate(value=self.value)

    @classmethod
    def help(cls):
        return 'Simply the text.'

    def __repr__(self):

        return f'<text {self.value!r}>'


class Attribute(Com):
    key: str
    values: t.Tuple[str, ...]

    @classmethod
    def new(cls, key=None, values=None):
        self = cls()
        self.key = key
        self.values = values
        return self

    def lens(self, key=None, values=None):
        new = Attribute()
        new.key = key or self.key
        new.values = values or self.values
        return new

    def to_node(self):
        tag = node.AttributeNode()
        tag.key = self.key
        tag.values = self.values
        return tag

    @classmethod
    def help(cls):
        return 'Simply the attribute.'

    def __repr__(self):
        attr = f'{self.key} = {" ".join(map(str, self.values))}>'
        return f'<attr {attr!r}>'


class Tag(Com):
    name: str
    components: t.Tuple[Com, ...]

    @classmethod
    def new(cls, name=None, components=None):
        self = cls()
        self.name = name
        self.components = tuple(components)
        return self

    def lens(self, name=None, components=None):
        new = Tag()
        new.name = name or self.name
        new.components = components or self.components
        return new

    def to_node(self):
        tag = node.TagNode()
        tag.name = self.name
        tag.children = tuple(each.to_node() for each in self.components)
        return tag

    @classmethod
    def help(cls):
        return 'Simply the tag.'

    def __repr__(self):
        return f'<tag name={self.name}>'
