# 1) render blog pages and search pages
# 2) define templates
# 3) DEFINE FOLDERS FOR SYNCEDFILE STORAGE AND IMAGES OUTPUT AND KEEP IT CLEAN (no more than X Gb)

# 4) implement command queue reading too


from flask import Flask, render_template, send_from_directory, request, make_response, g, abort
from toycommons import ToyInfra
from toycommons.drive.synced import SyncedFile
from pathlib import Path
from os import getenv
from blog import Blog
from blog.render import TailwindRender
from datetime import date
from dateutil.relativedelta import relativedelta

PERPAGE = 10

def cleanup_render():
    """
    Clear the render folder via config attribute (check sys datetime created)
    :return:
    """
    pass


app = Flask('blog')

tc = ToyInfra('blog', user=getenv('MONGO_USER'), passwd=getenv('MONGO_PASSWORD'))


blog_config = tc.get_own_config()

app.root_path = str(Path(app.root_path).parent)
app.static_folder = blog_config.data.get('render_path', 'render')
app.template_folder = 'blog_web/templates'
app.config['passwords'] = {}

blog = Blog(drive=tc.drive)

@app.before_request
def check_auth():
    g.visible = False
    if (token := request.cookies.get('auth')) is not None:
        if token == blog_config.data.get('master_token'):
            g.visible = True


@app.route('/auth/<token>', methods=['GET'])
def auth(token):
    resp = make_response()
    resp.set_cookie('auth', token)
    return resp


@app.route('/', methods=['POST', 'GET'])
def index(tag_spec=None, range_override=None):  # search and search results with POST
    # todo csrf
    if request.method == 'POST' or tag_spec is not None or range_override is not None:
        active_tags = [q.strip() for q in request.form.get('tags', '').split(',') if q.strip() != ''] or tag_spec
        title = request.form.get('search')
        original_search = title
        if title == '':
            title = None
        date_from = None if request.form.get('date_from', '') == '' else date.fromisoformat(
            request.form.get('date_from'))
        date_to = None if request.form.get('date_to', '') == '' else date.fromisoformat(request.form.get('date_to'))
        if range_override is not None:
            date_from = range_override[0]
            date_to = range_override[1]
        pages = blog.search_pages(tags=active_tags, title=title, date_from=date_from, date_to=date_to, visible=g.visible)
        pages = pages[:200]  # hard limit here
    else:
        pages = blog.get_latest(PERPAGE, visible=g.visible)
        active_tags = []
        original_search = ''
        date_from = ''
        date_to = ''
    if active_tags is None:
        active_tags = []
    sources = blog.get_subfolders()
    return render_template('search.html', tags=sorted(blog.get_all_tags(visible=g.visible)), active_tags=active_tags, results=pages,
                           sources=sources, original_search=original_search or '', date_from=date_from, date_to=date_to,
                           visible=g.visible, perpage=PERPAGE, url=tc.get_self_url(origin=request.origin, headers=request.headers))


@app.route('/tag/<tag>')
def tag(tag):
    return index(tag_spec=[tag])


@app.route('/date/<year>/')
@app.route('/date/<year>/<month>/')
@app.route('/date/<year>/<month>/<day>/')
def daterange(year, month=None, day=None):
    year = int(year)
    if month is not None:
        if day is not None:
            date_from = date(year=year, month=int(month), day=int(day))
            date_to = date_from
        else:
            date_from = date(year=year, month=int(month), day=1)
            date_to = date_from + relativedelta(months=1) - relativedelta(days=1)
    else:
        date_from = date(year=int(year), month=1, day=1)
        date_to = date_from + relativedelta(years=1) - relativedelta(days=1)
    return index(range_override=(date_from, date_to))

@app.route('/page/<page_id>:<token>')
def access_page(page_id, token):
    if token in app.config['passwords'].get(page_id, []):
        g.visible = True

    return render_page(page_id, suppress_share=True)

@app.route('/page/<page_id>', methods=['POST', 'GET'])
def render_page(page_id, suppress_share=False):
    if request.method == 'POST' and g.visible:
        pwd = request.form.get('password')
        if page_id not in app.config['passwords']:
            app.config['passwords'][page_id] = []
        if pwd in app.config['passwords'][page_id]:
            app.config['passwords'][page_id].remove(pwd)
        else:
            app.config['passwords'][page_id].append(pwd)

    page = blog.get_page_by_id(page_id)
    if not page.visible and not g.visible:
        return abort(404)
    body = blog.get_page_body(page)
    render_path = blog_config.data.get('render_path', 'render')
    for img in body.images:
        p = Path(render_path).joinpath(Path(page_id))
        p.mkdir(exist_ok=True, parents=True)
        p = str(p.joinpath(Path(img)))
        with open(p, 'wb') as f:
            f.write(body.images[img])
    render = TailwindRender(image_path_prepend=str(page_id)).render(page, body)
    if suppress_share:
        show_share = False
    else:
        show_share = g.visible
    return render_template('page.html', title=page.title, created_at=str(page.created_at),
                           original_url=page.original_url, render=render, tags=page.tags, show_share=show_share,
                           url=tc.get_self_url(origin=request.origin, headers=request.headers))


@app.route('/page/<page_id>/<filename>')
def get_file(page_id, filename):
    # send from directory is used due to send_static behaving weirdly.
    p = Path(app.root_path).joinpath(Path(app.static_folder)).joinpath(Path(page_id))
    return send_from_directory(p, filename)


@app.route('/templates/<file>')
def get_static(file):
    return send_from_directory(app.template_folder, file)


@app.route('/calendar')
def calendar():
    return render_template('calendar.html', url=tc.get_self_url(origin=request.origin, headers=request.headers))


@app.route('/calendar/data')
def calendar_data():
    # todo: csrf
    return blog.get_dates()


@app.route('/tags')
def all_tags():
    tags = blog.get_all_tags_with_count()
    tags = [(k, tags[k]) for k in sorted(tags.keys())]
    return render_template('tags.html', tags=tags, url=tc.get_self_url(origin=request.origin, headers=request.headers))
