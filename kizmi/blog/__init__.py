from kizmi import base
from kizmi.materialize import com as css
from kizmi.materialize import trait
from kizmi.module import index


class Article:
    title: str
    date: str
    content: str


def index_page():
    card = index.classic_card(
        title='一张卡片', content="人被杀，就会死", links={'link': '#2'})

    page = index.index_page(
        title='首页',
        logo_href='https://github.com/thautwarm',
        logo_name='Logo',
        navbar_contents=[
            index.timezone(),
            base.A(*base.attrs(href='#1'), base.text("simple test"))
        ],
        coms=[base.Div(trait.Container(), card)]).to_node()

    return page
