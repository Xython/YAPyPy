from kizmi import com, base, utils
import typing as t


class Color(com.Attribute):
    def update(self, major=None, micro=None, degree=None):
        return Color(major or self.major, micro or self.micro,
                     degree if degree is not None else self.degree)

    @property
    def major(self):
        return self.values[0]

    @property
    def micro(self):
        return self.values[1] if len(self.values) >= 2 else 'lighten'

    @property
    def degree(self):
        return self.values[2] if len(self.values) >= 3 else 0

    def __init__(self, major: str, micro: str = 'lighten', degree: int = 0):
        self.key = 'class'
        if degree < 0:
            micro = 'lighten' if micro == 'darken' else 'darken'

        self.values = (major, *(() if degree is 0 else (micro, degree)))

    @classmethod
    @utils.auto_doc
    def help(cls) -> str:
        """
        see http://archives.materializecss.com/0.100.2/color.html
        >>> from kizmi.materialize.css import helpers
        >>> helpers.Color('purple')
        >>> assert helpers.Color('purple', 'darken', -1) == helpers.Color('purple', 'lighten', 1)
        a collection of commonly used colors:
        - cyan
        - pink
        - deep-purple
        - teal
        - lime
        ...
        """


class SetClassAttribute(type):
    def __new__(mcs, name: str, bases, dict):
        cls = type(name, (*bases, com.Attribute), dict)
        cls.key = 'class'
        cls.values = name.lower(),
        return cls


class Container(metaclass=SetClassAttribute):
    pass


class Row(metaclass=SetClassAttribute):
    pass


class Divider(metaclass=SetClassAttribute):
    pass


class Section(metaclass=SetClassAttribute):
    pass


class FlowText(metaclass=SetClassAttribute):
    # noinspection PyMissingConstructor
    def __init__(self):
        self.values = 'flow-text'


class _Grid:
    def __init__(self,
                 s: t.Optional[int] = None,
                 m: t.Optional[int] = None,
                 l: t.Optional[int] = None):
        self.s = s
        self.m = m
        self.l = l

    def get_grids(self):
        s, m, l = self.s, self.m, self.l
        if s is not None:
            yield f's{s}'
        if m is not None:
            yield f'm{m}'
        if l is not None:
            yield f'l{l}'

    def update(self, s=None, m=None, l=None):
        return self.__class__(self.s if s is None else s,
                              self.m if m is None else m,
                              self.l if l is None else l)


class Col(com.Attribute, _Grid):
    key = 'class'

    @property
    def values(self):
        # noinspection PyRedundantParentheses
        return ('col', *self.get_grids())


class Align(com.Attribute):
    key = 'class'

    def __init__(self):
        self.which = None

    def lens(self, key=None, values=None):
        raise TypeError

    @property
    def values(self):
        return f'{self.which}-align',

    @classmethod
    def _align(cls, align_name):
        new = cls()
        new.which = align_name
        return new

    @classmethod
    def left(cls):
        return cls._align('left')

    @classmethod
    def right(cls):
        return cls._align('right')

    @classmethod
    def center(cls):
        return cls._align('center')


class Truncate(metaclass=SetClassAttribute):
    pass


class Push(com.Attribute, _Grid):
    key = 'class'

    @property
    def values(self):
        # noinspection PyRedundantParentheses
        return tuple(map('push-'.__add__, self.get_grids()))


class Pull(com.Attribute, _Grid):
    key = 'class'

    @property
    def values(self):
        # noinspection PyRedundantParentheses
        return tuple(map('pull-'.__add__, self.get_grids()))


class Offset(com.Attribute, _Grid):
    key = 'class'

    @property
    def values(self):
        # noinspection PyRedundantParentheses
        return tuple(map('offset-'.__add__, self.get_grids()))


class Circle(com.Attribute):
    pass


class Pulse(metaclass=SetClassAttribute):
    pass


class Depth(com.Attribute):
    key = 'class'

    def __init__(self, depth: int):
        self.depth = depth

    @property
    def values(self):
        return f"z-depth-{self.depth}",

    def update(self, depth=None):
        return Depth(depth if depth is None else self.depth)


class Option(com.Attribute):
    key = "data-badge-caption"

    def __init__(self, text: str):
        self.values = text,


class Button(com.Attribute):
    key = 'class'
    values = 'btn',


class FloatingButton(com.Attribute):
    key = 'class'
    values = 'btn-floating'


class Horizontal(metaclass=SetClassAttribute):
    pass


class Submit(com.Attribute):
    key = 'type'
    values = 'submit',


class Disabled(metaclass=SetClassAttribute):
    pass


class Breadcrumb(metaclass=SetClassAttribute):
    pass


class Chip(metaclass=SetClassAttribute):
    pass
