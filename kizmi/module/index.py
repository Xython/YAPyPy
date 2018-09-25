import kizmi.base as base
import kizmi.com as com
import kizmi.materialize.com as css
import kizmi.materialize.trait as trait
from toolz import curry, compose

import datetime
import typing as t


class MComp:
    def __init__(self, func=lambda it: it):
        self.func = func

    def __or__(self, item):
        return MComp(compose(item, self.func))

    def __call__(self, arg):
        if arg is None:
            return ()

        res = self.func(arg)
        if res is None:
            return ()

        return res,


m_comp: MComp = MComp()


@curry
def apply(it, f):
    """
    bind for maybe
    """
    return f(it)


def timezone():
    return base.text(
        str(datetime.datetime.now().strftime('%y-%m-%d %H:%M %p')))


def index_page(title=None,
               logo_href="#",
               logo_name="Logo",
               navbar_contents: t.Iterable[com.Com] = (),
               coms: t.Iterable[com.Com] = ()):

    return base.HTML(
        css.MaterializeHead(*apply(title, m_comp | base.text | base.Title)),
        base.Nav(
            css.NavWrapper(
                css.Logo(
                    logo_href or '#',
                    *apply(logo_name, m_comp | base.text),
                ),
                base.Ul(
                    base.simple_attr('class', 'right'),
                    *[base.Li(each) for each in navbar_contents]))), *coms)


_teal = trait.Color(major='teal')


def classic_card(img: t.Union[str, t.Dict[str, str]] = None,
                 title: str = None,
                 content: str = None,
                 links: t.Dict[str, str] = None,
                 color: str = None):
    def make_img(img):
        if isinstance(img, str):
            return base.Img(*base.attrs(src=img))

        if isinstance(img, dict):
            return base.Img(**img)

    def make_links(links):
        return [
            base.A(*base.attrs(href=link), base.text(name))
            for name, link in links.items()
        ]

    return css.Card(
        *apply(color, m_comp | trait.Color), *apply(img, m_comp | make_img),
        css.CardContent(
            *apply(title, m_comp | base.text | css.CardTitle),
            *apply(content, m_comp | base.text),
        ), *apply(links, m_comp | make_links | css.CardAction))
