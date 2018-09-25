import kizmi.base as base
import kizmi.com as com
import kizmi.materialize.com as css
import kizmi.materialize.trait as trait
from kizmi.module import index
from sanic import Sanic

from sanic import response

app = Sanic(__name__)


@app.route('/')
async def main(request):
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
    return response.html(page.dumps())


app.run(port=80, debug=True)
