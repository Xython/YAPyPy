from kizmi import com, node, utils
import typing as t


def fix_tag_name(cls: t.Type[com.Tag]):
    cls.name = cls.__name__.lower()
    return cls


def fix_attr_name(cls: t.Type[com.Attribute]):
    cls.key = cls.__name__.lower()
    return cls


class FixedNamedTag(com.Tag):
    _fixed_attrs = {}

    def __init__(self, *coms: com.Com):
        if self._fixed_attrs:
            coms = (*coms,
                    *(simple_attr(k, v) for k, v in self._fixed_attrs.items()))

        self.components = coms

    @classmethod
    def help(cls):
        name = cls.__name__
        return f'A tag with fixed name {name}.'


class FixedNamedAttr(com.Attribute):
    def __init__(self, *values: str):
        self.values = values

    @classmethod
    def help(cls):
        name = cls.__name__
        return f'An attribute with fixed name {name}.'

    def lens(self, *args, **kwargs):
        """
        invalid operation
        """
        raise TypeError


def attrs(**kwargs):
    return (simple_attr(k, v) if v is not None else simple_attr(k)
            for k, v in kwargs.items())


def text(content: t.Union[str, t.Iterable[str]]):
    """
    make raw text
    """

    def f(s):
        ret = com.Texture()
        ret.value = s
        return ret

    return utils.map_with_shape(f)(content)


@fix_attr_name
class Src(FixedNamedAttr):
    pass


@fix_tag_name
class HTML(FixedNamedTag):
    pass


@fix_tag_name
class Title(FixedNamedTag):
    pass


@fix_tag_name
class Html(FixedNamedTag):
    pass


@fix_tag_name
class Div(FixedNamedTag):
    pass


@fix_tag_name
class I(FixedNamedTag):
    pass


@fix_tag_name
class Head(FixedNamedTag):
    pass


@fix_tag_name
class Meta(FixedNamedTag):
    pass


@fix_tag_name
class Body(FixedNamedTag):
    pass


js_script_attr = com.Attribute()
js_script_attr.key = 'type'
js_script_attr.values = ('text/javascript', )


@fix_tag_name
class Script(FixedNamedTag):
    def __init__(self, *coms):
        super().__init__(*coms, js_script_attr)


@fix_tag_name
class Link(FixedNamedTag):
    pass


@fix_tag_name
class A(FixedNamedTag):
    pass


@fix_tag_name
class Li(FixedNamedTag):
    pass


@fix_tag_name
class Ul(FixedNamedTag):
    def __init__(self, *coms: com.Com):
        super().__init__(*coms)


@fix_tag_name
class Span(FixedNamedTag):
    pass


@fix_tag_name
class Nav(FixedNamedTag):
    pass


@fix_tag_name
class P(FixedNamedTag):
    pass


@fix_tag_name
class Img(FixedNamedTag):
    pass


def simple_tag(name, content):
    return com.Tag.new(name=name, components=(content, ))


def simple_attr(key, *values):
    return com.Attribute.new(key=key, values=values)
