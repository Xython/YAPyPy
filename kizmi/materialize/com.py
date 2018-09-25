from kizmi.materialize import trait
from kizmi import com, base, utils
import typing as t
responsive_img_attr = com.Attribute()
responsive_img_attr.values = 'responsive-img',
responsive_img_attr.key = 'class'


class RespImg(com.Tag):
    name = 'img'

    def __init__(self, src: str, *coms):
        self.components = (responsive_img_attr, *coms, base.Src(src))


_vc_attr = com.Attribute.new(key='class', values=('video-container', ))


class VideoContainer(base.Div):
    def __init__(self,
                 src,
                 width: int = 853,
                 height: int = 480,
                 frameborder=0,
                 allowfullscreen=True,
                 *coms):
        self.src = src
        self.width = width
        self.height = height
        self.frameborder = frameborder
        self.allowfullscreen = allowfullscreen
        self.other_components = tuple(coms)

    @property
    def components(self):
        iframe = com.Tag.new(
            name='iframe',
            components=(com.Attribute.new(key='width', values=(self.width, )),
                        com.Attribute.new(
                            key='height', values=(self.height, )),
                        com.Attribute.new(
                            key='frameborder', values=(self.frameborder, )),
                        *((com.Attribute.new(key='allowfullscreen', values=()))
                          if self.allowfullscreen else
                          ()), *self.other_components))
        return _vc_attr, iframe


class THead(com.Tag):
    name = 'thead'

    def __init__(self, column_names: t.List[str], *coms):
        self.column_names = column_names
        self.other_coms = coms

    @property
    def components(self):
        cols = [
            com.Tag.new(name='th', components=base.text(col))
            for col in self.column_names
        ]
        tr = com.Tag.new(name='tr', components=tuple(cols))

        return (tr, *self.other_coms)


class TBody(com.Tag):
    name = 'tbody'

    def __init__(self, data: t.List[t.List[com.Com]], *coms):
        self.data = data
        self.other_coms = coms

    @property
    def components(self):
        return (*(com.Tag.new(
            name='tr',
            components=tuple(base.simple_tag('td', cell) for cell in row))
                  for row in self.data), *self.other_coms)


class Table(com.Tag):
    name = 'table'

    def __init__(self, thead: THead, tbody: TBody, *coms: com.Com):
        self.components = (thead, tbody, *coms)


collection_attr = com.Attribute.new(key='class', values=('collection'))


class CollectionHeader(base.FixedNamedTag):
    _fixed_attrs = {'class': 'collection-header'}

    def __init__(self, tag: com.Tag, *coms):
        self.name = tag.name
        super().__init__(*tag.components, *coms)


class CollectionItem(base.FixedNamedTag):
    _fixed_attrs = {'class': 'collection-item'}

    def __init__(self, tag: com.Tag, *coms):
        self.name = tag.name
        super().__init__(*tag.components, *coms)


class Collection(base.FixedNamedTag):
    _fixed_attrs = {'class': 'collection'}

    def __init__(self, tag: com.Tag, collection_items: t.List[CollectionItem],
                 *coms):

        self.name = tag.name
        super().__init__(*tag.components, *collection_items, *coms)


class DropdownActivator(base.A):
    def __init__(self, id: str, *coms):
        super().__init__(base.simple_attr('data-activates', id), *coms)


class Dropdown(base.Ul):
    def __init__(self, id: str, items: t.List[base.Li], *coms: com.Com):
        self.id = id
        super().__init__(
            base.simple_attr('id', id),
            base.simple_attr('class', 'dropdown-content'), *items, *coms)

    def activator(self, *coms):
        return DropdownActivator(self.id, *coms)


class Logo(base.A):
    _fixed_attrs = {'class': 'brand-logo'}

    def __init__(self, href: str, *coms):
        super().__init__(base.simple_attr('href', href), *coms)


class NavWrapper(base.Div):
    _fixed_attrs = {'class': 'nav-wrapper'}

    def __init__(self, logo: Logo, ul: base.Ul, *coms):
        super().__init__(logo, ul, *coms)


class Icon(base.I):
    _fixed_attrs = {'class': 'material-icons'}

    def __init__(self, icon_name: str, *coms):
        super().__init__(base.text(icon_name), *coms)


class Badge(base.Span):
    _fixed_attrs = {'class': 'badge'}


class CollapsibleHeader(base.Div):
    def __init__(self, icon: Icon, badge: Badge, *coms: com.Com):
        super().__init__(icon, badge, *coms)


class Collapsible(base.Ul):
    _fixed_attrs = {'class': 'collapsible', 'data-collapsible': 'accordion'}

    def __init__(self, headers: t.List[CollapsibleHeader], *coms):
        super().__init__(*map(base.Li, headers), *coms)


class FAB(base.Div):
    _fixed_attrs = {'class': 'fixed-action-btn'}

    def __init__(self, floating_btn: trait.FloatingButton, ul: base.Ul, *coms):
        super().__init__(floating_btn, ul, *coms)


class CardImg(base.Div):
    _fixed_attrs = {'class': 'card-image'}

    def __init__(self, img: base.Img, *coms):
        super().__init__(img, *coms)


class CardTitle(base.Span):
    _fixed_attrs = {'class': 'card-title'}
    pass


class CardContent(base.Div):
    _fixed_attrs = {'class': 'card-content'}

    def __init__(self, *coms, title: t.Optional[CardTitle] = None):
        super().__init__(*([title] if title else ()), *coms)


class CardAction(base.Div):
    _fixed_attrs = {'class': 'card-action'}

    def __init__(self, a_lst: t.Iterable[base.A] = (), *coms):
        super().__init__(*a_lst, *coms)


class Card(base.Div):
    _fixed_attrs = {'class': 'card'}

    def __init__(self, *stuffs: t.Union[CardAction, CardContent, CardImg]):
        super().__init__(*stuffs)


js_include = (
    base.Script(
        base.simple_attr('type', 'text/javascript'),
        base.simple_attr('src',
                         'https://cdn.bootcss.com/jquery/3.2.1/jquery.js'),
        base.text('')),
    base.Script(
        base.simple_attr(
            'src',
            'https://cdn.bootcss.com/materialize/1.0.0-rc.1/js/materialize.min.js'
        ), base.text('')))

font_link = base.Link(
    base.simple_attr(
        'href', 'https://fonts.googleapis.com/icon?family=Material+Icons'),
    base.simple_attr('rel', 'stylesheet'))

css_link = base.Link(
    base.simple_attr(
        'href',
        'https://cdn.bootcss.com/materialize/1.0.0-rc.1/css/materialize.min.css'
    ), base.simple_attr('rel', 'stylesheet'))

view_point = base.Meta(
    base.simple_attr('name', 'viewpoint'),
    base.simple_attr('content', 'width=device-width, initial-scale=1.0'))
charset = base.Meta(base.simple_attr('charset', 'utf-8'))


class MaterializeHead(base.Head):
    def __init__(self, *coms: com.Com):
        super().__init__(font_link, css_link, view_point, charset, *js_include,
                         *coms)
