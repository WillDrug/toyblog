from http.client import RemoteDisconnected
from typing import Iterable
from PIL import Image as PILImage
from io import BytesIO
import requests
import pickle
from time import sleep
from dataclasses import dataclass, field, asdict
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request, quote
from urllib.error import HTTPError, URLError
from hashlib import sha512
import tqdm
from blog import Page, Container, Indent, Italic, Bold, Align, Text, Glyph, Image, Display, Spoiler, NewLine, URL, \
    GlyphType, Small, Large, Muted, Paragraph, VideoEmbed, LineBreak, OriginalStyle, Strikethrough, Header, \
    Underline, Color, Size, Monospace, Surrounded, List, ListElement, SectionBreak, Margin
from blog.model import VideoEmbedType
from datetime import date
import re
from copy import deepcopy
import sys
from hashlib import md5

sys.setrecursionlimit(50000)


class ImageRef:
    def __init__(self, url, base_prefix=None):
        self.base_prefix = base_prefix
        self.original_url = url
        self.data = None
        self.error = False
        self.error_message = None
        if not url.startswith('http'):
            url = self.base_prefix + '/' + url
        if '\r' in url:
            url = url.split('\r')[0] + url.split('\n')[-1]
        url = url[:7] + quote(url[7:])
        self.request_url = url
        name = url.split('?')[0].split('/')[-1]
        if '.' not in name:
            if 'png' in url:
                name += '.png'
            elif 'gif' in url:
                name += '.gif'
            else:
                name += '.jpg'  # default to jpg why not?..
        if len(name) > 50 or quote(url[7:]) != url[7:]:
            name = md5(name.encode('utf-8')).hexdigest() + '.' + name.split('.')[-1]
        self.name = name

    def load_data(self):
        try:
            op = requests.get(self.request_url, verify=False)
            self.data = op.content
            test = PILImage.open(BytesIO(self.data))
            self.name = self.name.split('.')[0] + '.' + test.format
            self.error = False
            self.error_message = None
        except Exception as e:
            self.error = True
            self.error_message = e


class CrawlerBlogPage:
    def __init__(self, created_at, data, tags=None, title=None):
        self.created_at = created_at
        self.data = data
        self.tags = tags
        self.title = title


class CrawlerPage:
    def __init__(self, web_url, unique_id, parsed=False, loaded=False, data=None, blog_data=None, listing_url=None):
        self.web_url = web_url
        self.unique_id = unique_id
        self.parsed = parsed
        self.loaded = loaded
        self.data = data  # hold as str(soup), load as BeuaitfulSoup(data, 'lxml');
        self.blog_data = blog_data  # Page object. held as Page object.
        self.listing_url = listing_url
        self.errors = 0
        self.error_loading = False
        self.offload_error = False
        self.image_ref = None

    def load_image_ref(self):
        try:
            with open(f'data/imgref/imgref-{self.unique_id}', 'rb') as f:
                self.image_ref = pickle.loads(f.read())
        except FileNotFoundError:
            self.image_ref = {}

    def dump_image_ref(self):
        with open(f'data/imgref/imgref-{self.unique_id}', 'wb') as f:
            f.write(pickle.dumps(self.image_ref))
        self.image_ref = None

    def __eq__(self, other):
        if isinstance(other, str):
            return self.unique_id == other
        return self.unique_id == other.unique_id

    def __repr__(self):
        state = 'blank' if not self.loaded else 'loaded' if not self.parsed else 'parsed'
        return f'<CrawlerPage({self.web_url} :: {self.unique_id} ! {state} ({self.errors}) [{"x" if self.error_loading else ""}])>'

    def get_data(self):
        return BeautifulSoup(self.data, 'lxml')


class Listing:
    def __init__(self, url):
        self.url = url
        self.crawled = False

    def __eq__(self, other):
        if not isinstance(other, Listing):
            return self.url == other
        return self.url == other.url

    def __repr__(self):
        return f'<Listing({self.url} [{"x" if self.crawled else ""}])>'


@dataclass
class CrawlerMeta:
    pages: list[CrawlerPage] = field(default_factory=list)
    listings: list[Listing] = field(default_factory=list)
    auth: str = None


class Crawler:
    def __init__(self, loader, auth=None):
        loaded = False
        try:
            with open(f'data/{loader.__name__}.pcl', 'rb') as f:
                self.__db = CrawlerMeta(**pickle.loads(f.read()))
            loaded = True
        except FileNotFoundError:
            self.__db = CrawlerMeta()
        if auth is not None:
            self.__db.auth = auth
        self.loader = loader(self.__db.auth)
        if not loaded:
            self.save()

    def get_all_pages(self):
        return self.__db.pages

    def get_all_listings(self):
        return self.__db.listings

    def save(self):
        savedata = pickle.dumps(asdict(self.__db))
        with open(f'data/{self.loader.__class__.__name__}.pcl', 'wb') as f:
            f.write(savedata)

    def add_listing(self, url):
        self.__db.listings.append(Listing(url))
        self.save()

    def crawl(self, base_url=None, force=False, single_listing=None) -> str | None:
        """
        Takes an expected Loader base url, populates CrawlerMeta pages with urls.
        :param base_url: URL to whatever base required by loader
        :param force: Overwrite data
        :return: Error \ None
        """
        if single_listing is not None:
            single_listing = Listing(single_listing)
            if single_listing not in self.__db.listings:
                self.__db.listings.append(single_listing)
            pages = self.loader.crawl([single_listing])
            for page in pages:
                if page not in self.__db.pages:
                    self.__db.pages.append(page)
                elif force:
                    self.__db.pages.remove(page)
                    self.__db.pages.append(page)
        if self.__db.listings.__len__() == 0 or force:
            print('Updating listings')
            if base_url is None:
                raise AttributeError(f'Provide base url for the crawl')
            try:
                pages = self.loader.get_crawl_targets(base_url)
                for page in pages:
                    if page not in self.__db.listings:
                        self.__db.listings.append(Listing(page))
            except Exception as e:
                return f'{e.__class__}: {str(e)}'
        print('Processing non-crawled listings')
        pages = self.loader.crawl([q for q in self.__db.listings if not q.crawled])
        if force:
            self.__db.pages = pages
        else:
            for page in pages:
                if page not in self.__db.pages:
                    self.__db.pages.append(page)
        self.save()

    def get_page_by_id(self, page_id) -> CrawlerPage:
        return next((q for q in self.__db.pages if q.unique_id == page_id), None)

    def get_page_by_url(self, url) -> CrawlerPage:
        return next((q for q in self.__db.pages if q.web_url == url), None)

    def parse_page(self, page: CrawlerPage) -> bool:
        self.loader.parse_page(page)
        page.parsed = True

    def parse_pages(self, force=False):
        """
        Go through page data and turn into blog content.
        :param force: Doesn't ignore already processed
        :return:
        """
        for page in tqdm.tqdm(self.__db.pages):
            if not page.parsed or force:
                try:
                    self.parse_page(page)
                    page.error_loading = False
                    page.parsed = True
                except Exception as e:
                    page.error_loading = True
                    page.parsed = False
                    print(f'Page {page.web_url} failed with {e.__class__}: {e.__str__()}')
        self.save()

    def add_page(self, url):
        page = CrawlerPage(url, unique_id=self.loader.get_id_from_data(data))
        self.loader.load_page(page)
        self.__db.pages.append(page)

    def load_page(self, page):
        """
        Load bytes of a single page
        :param page: Page object.
        :return:
        """
        try:
            self.loader.load_page(page)
            # page.data = str(self.loader.load_page(page.web_url))
        except Exception as e:
            page.error_loading = e
            print(f'Failed to load page {page.web_url}, error {e.__class__}: {e.__str__()}')
        else:
            page.loaded = True

    def fix_listings(self):
        listings = [Listing(z) for z in list(set([q.listing_url for q in self.__db.pages if not q.error_loading])) if
                    z is not None]
        print(f'Got {len(listings)} to recrawl')
        self.__db.pages = [q for q in self.__db.pages if q.listing_url not in listings]
        pages = self.loader.crawl(listings)
        self.__db.pages.extend(pages)
        self.save()

    def clear_listings(self):
        self.__db.listings = []

    def clear_pages(self):
        self.__db.pages = []

    def load_pages(self, force=False):
        """
        Go through pages and load their data if unloaded
        :param force: Doesn't ignore already loaded
        :return:
        """
        for page in tqdm.tqdm(self.__db.pages):
            if not page.loaded or force or page.error_loading:
                page.error_loading = False
                self.load_page(page)
        self.save()

    def build_img_ref(self, page: CrawlerPage):
        image_ref = {}

        def process(data):
            if isinstance(data, Image):
                if data.data is None:
                    return
                ref = ImageRef(data.data, base_prefix=self.loader.base_image_prefix)
                image_ref[ref.original_url] = ref

            elif isinstance(data.data, Iterable) and not isinstance(data.data, str):
                for d in data.data:
                    process(d)

        process(page.blog_data.data)
        page.image_ref = image_ref
        page.dump_image_ref()

    def load_img_ref(self, page: CrawlerPage, force=False):
        page.load_image_ref()
        if page.image_ref is None:
            return
        for image in page.image_ref:
            if page.image_ref[image].data is None or force:
                page.image_ref[image].load_data()
        page.dump_image_ref()

    def get_blog_data_with_img_ref_names(self, page: CrawlerPage):
        data = deepcopy(page.blog_data.data)

        def process(data):
            if isinstance(data, Image):
                if data.data is None:
                    return
                ref = page.image_ref.get(data.data)
                if ref is not None and not ref.error:
                    data.data = ref.name
            elif isinstance(data.data, Iterable) and not isinstance(data.data, str):
                for d in data.data:
                    process(d)

        process(data)
        return data

    def get_url_binary_data(self, url, retry_codes=[429]):
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'
        }

        req = Request(url, headers=hdr)
        # print(url)

        retry = 0
        max_retries = 3
        slp = 5
        done = False

        while not done:
            try:
                op = urlopen(req, timeout=10)
                reader = op.fp
                data = reader.read()
                done = True
            except HTTPError as e:
                if e.status in retry_codes:
                    print(f'Got {e.status}, sleeping for {slp} seconds. Retry {retry}/{max_retries}')
                    sleep(slp)
                else:
                    return None

                if retry >= max_retries:
                    print(f'Failed on {url}')
                    return

                retry += 1

            except URLError:
                return None
            except RemoteDisconnected:
                return None
            except ConnectionResetError:
                return None
            except TimeoutError:
                return None
            except UnicodeEncodeError:
                return None

        return data


class Loader:
    base_image_prefix = ''
    page_type = None

    def __init__(self, auth):
        self.auth = auth
        if auth is None:
            print(f'No auth provided to the loader. Results may vary.')

    def get_crawl_targets(self, base_url) -> list[str]:
        raise NotImplementedError(f'Specify a loader')

    def crawl(self, urls: list[Listing]) -> list[CrawlerPage]:
        raise NotImplementedError(f'Specify a loader')

    def load_page(self, page):
        raise NotImplementedError(f'Specify a loader')

    def parse_page(self, page_data):
        raise NotImplementedError(f'Specify a loader')

    def get_id_from_data(self, data):
        raise NotImplementedError(f'Specify a loader')


class DiaryLoader(Loader):
    base_image_prefix = 'https://diary.ru'
    page_type = 'diary'

    def __load_page(self, url):
        hdr = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'
        }
        if self.auth is not None:
            hdr['Cookie'] = f'_identity_={self.auth}'
        req = Request(url, headers=hdr)

        retry = 0
        max_retries = 3
        slp = 5
        done = False

        while not done:
            try:
                op = urlopen(req)
                done = True
            except HTTPError as e:
                if e.status == 429:
                    print(f'Got 429, sleeping for {slp} seconds. Retry {retry}/{max_retries}')
                    sleep(slp)
                if retry >= max_retries:
                    raise e
                retry += 1

        reader = op.fp
        data = reader.read().decode('utf-8', "replace").replace('\r\n8000\r\n', '')  # weird diary thing
        data = BeautifulSoup(data, "html5lib")
        return data

    def get_id_from_data(self, data):
        return f'diary-{sha512(data.encode()).hexdigest()[:8]}'

    def __get_page_links(self, page_listing) -> list[CrawlerPage]:
        try:
            data = self.__load_page(page_listing.url)
        except Exception as e:
            print(e.__class__, e)
            return [page_listing.url]
        try:
            return [CrawlerPage(q.attrs['href'].replace('\n', '').replace('\r', ''),
                                self.get_id_from_data(q),
                                listing_url=page_listing.url)
                    for q in data.find_all('a', string='URL')]
        finally:
            page_listing.crawled = True

    def get_crawl_targets(self, base_url) -> list[str]:
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        data = self.__load_page(base_url)
        pag = data.find('div', attrs={'id': 'pageBar'}).find(attrs={'class': 'pagination'})
        if pag is None:
            # single page diary
            fr = 20
            to = 21
        else:
            fr = int(pag.contents[-1].attrs['href'].split('=')[1])
            to = int(pag.contents[1].attrs['href'].split('=')[1])

        # generate all page links
        return [f'{base_url}?rfrom={q}' for q in range(fr, to + 1, 20)]

    def crawl(self, urls) -> list[CrawlerPage]:
        res = []
        for url in tqdm.tqdm(iterable=urls):
            res.extend(self.__get_page_links(url))
        return res

    def load_page(self, page: CrawlerPage):
        page.data = str(self.__load_page(page.web_url))
        # with open('preextend.html', 'w', encoding='utf-8') as f:
        #     f.write(page.data)
        self.extend_comment_section(page)
        # with open('postextent.html', 'w', encoding='utf-8') as f:
        #     f.write(page.data)

    def get_comment_range(self, page):
        data = BeautifulSoup(page.data, 'lxml')
        pag = data.find(attrs={'class': 'pagination'})
        if pag is None:
            return None
        last = pag.find(attrs={'class': 'last'}).attrs.get('href', '').split('=')[-1]
        last = int(last)  # can exception out here
        return range(last, 0, -30)

    def extend_comment_section(self, page):
        rng = self.get_comment_range(page)
        if rng is None:
            return
        data = BeautifulSoup(page.data, 'lxml')
        comments = data.find(attrs={'id': 'commentsArea'}).find(attrs={'class': 'pager_target'}).find('div')
        for page_num in reversed(rng):  # go from low page to high page
            retried = 0
            while True:
                try:
                    print(f'Loading comment page {page_num} for {page.web_url}')
                    page_data = self.__load_page(page.web_url + f'?from={page_num}')
                    page_comments = page_data.find(attrs={'id': 'commentsArea'}). \
                        find(attrs={'class': 'pager_target'}). \
                        find('div'). \
                        find_all(attrs={'class': 'singleComment'})
                    comments.contents.extend(page_comments)
                    break
                except Exception as e:
                    retried += 1
                    if retried < 2:
                        print(f'Loading comments failed with {e.__class__}: {e.__str__()}, retry {retried}')
                    else:
                        raise e
        page.data = str(data)

    def parse_page(self, page):
        # Title
        data = BeautifulSoup(page.data, 'lxml')
        title = str(''.join(data.find(attrs={'class': 'title'}).contents))

        # Created At
        months = {v: str(i + 1).zfill(2) for i, v in
                  enumerate(['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
                             'августа', 'сентября', 'октября', 'ноября', 'декабря'])}

        datestring = data.find(attrs={'class': 'countSecondDate'}).find('span').contents[0].split(',')[1].strip()
        for k in months:
            datestring = datestring.replace(k, months[k])

        d, m, y = datestring.split(' ')
        created_at = date(day=int(d), month=int(m), year=int(y))

        inner = data.find(attrs={'class': 'postInner'})
        tags_elem = inner.find(attrs={'class': 'tags atTag'})
        tags = []
        if tags_elem is not None:
            for url in tags_elem.find_all('a'):
                tags.append('\n'.join(url.contents))
            tags_elem.clear()

        inner = inner.find(attrs={'class': 'paragraph'})

        # Body
        # null off base
        self.errors = 0
        self.current_indent = 0

        root = Container([])  # root container.

        page_data = Container([], formatting=Display(display='row'))

        banner = Container([], formatting=[Size(width='10%'), Margin(left='10px', right='20px', top='20px'),
                                           OriginalStyle(style='min-width: 10%')])
        self.process(banner,
                     data.find('div', attrs={'class': 'postContent'}).find('div', attrs={'class': 'commentAuthor'}))
        page_data.data.append(banner)

        content = Container([])
        self.process(content, inner)
        page_data.data.append(content)
        root.data.append(page_data)

        root.data.append(SectionBreak(None))

        comments = data.find(attrs={'id': 'commentsArea'}).find(attrs={'class': 'pager_target'}). \
            find('div').find_all(attrs={'class': 'singleComment'})

        for comment in comments:
            comment_container = Container([])
            comment_container.data.append(Header([Text(''.join(comment.find(attrs={'class': 'postTitle'}).
                                                               find('span').contents))], size=4))
            inner_comment = Container([], formatting=Display(display='row'))
            # "banner"
            banner = Container([], formatting=[Size(width='10%'), Margin(left='10px', right='20px', top='5px')])

            banner.data.append(Text(''.join(comment.find(attrs={'class': 'authorName'}).find('strong').contents),
                                    formatting=Bold()))
            banner.data.append(NewLine(None))
            author = comment.find(attrs={'class': 'commentAuthor'})
            if author is not None:
                img = author.find('img')
                if img is not None:
                    banner.data.append(Image(str(img.attrs.get('src', '')), height=str(img.attrs.get('height', None)),
                                             width=str(img.attrs.get('width', None)),
                                             alt=str(img.attrs.get('alt', '')), formatting=Display(display='block')))
                sign = author.find(attrs={'class': 'sign'})
                if sign is not None:
                    banner.data.append(Text(''.join(sign.contents), formatting=[Small(), Italic()]))
            inner_comment.data.append(banner)
            # main content
            main = Container([])
            self.process(main, comment.find(attrs={'class': 'postInner'}).find(attrs={'class': 'paragraph'}))
            inner_comment.data.append(main)
            comment_container.data.append(inner_comment)
            # add all
            root.data.append(comment_container)
            root.data.append(NewLine(None))
        page.errors = self.errors
        page.blog_data = CrawlerBlogPage(created_at, root, tags=tags, title=title)

    def __quote(self, child, spf=None):
        self.current_indent += 1
        cont = Container([], formatting=Indent(steps=self.current_indent))
        self.process(cont, child, single_pass_formatting=spf)
        self.current_indent -= 1
        return cont

    def __spoiler(self, child, spf=None):
        cont = Container([])
        self.process(cont, child, single_pass_formatting=spf)
        sp = Spoiler([], spoiler_data=cont)
        self.process(sp, child.next_sibling, single_pass_formatting=spf)
        child.next_sibling.skip = True
        return sp

    def __url(self, child, spf=None):
        href = child.attrs.get('href', '')
        if not href.startswith('http'):
            href = 'https://diary.ru' + href
        url_data = URL([], tooltip=child.attrs.get('title'), href=href)
        if 'TagJIco' in child.attrs.get('class', []):
            url_data.data = [Glyph(GlyphType.diary_dog)]
        else:
            self.process(url_data, child, single_pass_formatting=spf)
        return url_data

    def __passthrough(self, child, spf=None) -> list:
        fc = Container([])
        self.process(fc, child, single_pass_formatting=spf)
        self.extended = True
        return fc.data

    def process(self, data, elem, single_pass_formatting=None) -> int:
        res = []
        for child in elem.contents:
            self.extended = False
            if not isinstance(child, str) and child.skip:
                continue
            if child == '\n':  # ignore random newlines. respect only BR.
                continue
            elif isinstance(child, str):
                if child.strip().__len__() == 0:
                    continue
                res.append(Text(str(child)))
            elif child.name.startswith('h') and child.name.__len__() == 2 and child.name[1].isdigit():
                ida = self.__passthrough(child)
                res.append(Header(ida, size=int(child.name[1])))
            elif child.name == 'noindex':
                res.extend(self.__passthrough(child, spf=single_pass_formatting))
            elif child.name == 'embed-error':
                res.append(Text('<This was a media. It doesn\'t exist anymore.>'))
            elif child.name == 'ul':
                l = List([])
                self.process(l, child)
                res.append(l)
            elif child.name == 'li':
                l = ListElement([])
                self.process(l, child)
                res.append(l)
            elif child.name == 'textarea':
                c = Container([])
                self.process(c, child, single_pass_formatting=single_pass_formatting)
                res.append(c)
            elif child.name == 'img':
                # download image, add IOBuffer to object as data
                res.append(Image(str(child.attrs.get('src', '')), height=str(child.attrs.get('height', None)),
                                 width=str(child.attrs.get('width', None)),
                                 alt=str(child.attrs.get('alt', ''))))
            elif child.name == 'br':
                res.append(NewLine(None))
            elif child.name == 'a':
                if 'LinkMore' in child.attrs.get('class', []):
                    res.append(self.__spoiler(child))
                else:
                    if child.contents.__len__() == 0:
                        continue
                    res.append(self.__url(child))
            elif child.name == 'blockquote':
                res.append(self.__quote(child))
            elif child.name == 'div':
                if 'blockquote' in child.attrs.get('class', []):
                    res.append(self.__quote(child))
                elif 'sign' in child.attrs.get('class', []):
                    res.append(Text(''.join(child.contents), formatting=[Small(), Italic()]))
                else:
                    formatting = None
                    if 'align' in child.attrs:
                        formatting = Align(position=child.attrs['align'])
                    next = Container([], formatting=formatting)
                    self.process(next, child)
                    if next.data.__len__() == 0:
                        continue
                    res.append(next)
            elif child.name == 'span':
                if 'quote_text' in child.attrs.get('class', []):
                    bcl = child.find('blockquote')
                    if bcl is None:
                        bcl = child.find('div', attrs={'class': 'blockquote'})
                    if bcl is None:  # regular text
                        res.extend(self.__passthrough(child, spf=single_pass_formatting))
                    else:
                        res.append(self.__quote(bcl))
                else:
                    spf = None
                    if 'offtop' in child.attrs.get('class', []):
                        if single_pass_formatting is not None:
                            if not isinstance(single_pass_formatting, Iterable):
                                spf = [Muted(), single_pass_formatting]
                            else:
                                spf = single_pass_formatting + [Muted()]
                        else:
                            spf = Muted()
                    res.extend(self.__passthrough(child, spf=spf))
            elif child.name == 'p':
                c = Paragraph([])
                self.process(c, child)
                if c.data.__len__() == 0:
                    continue
                res.append(c)
            elif child.name == 'font':
                to_pass = []
                if child.attrs.get('size') is not None:
                    try:
                        sz = child.attrs.get('size', '').split(';')[-1]
                        sz = int(sz)
                        if sz < 0:
                            to_pass.append(Small())
                        else:
                            to_pass.append(Large())
                    except ValueError:
                        pass  # values like "7px" are ignored, screw it.
                if child.attrs.get('color') is not None:
                    to_pass.append(Color(color=child.attrs.get('color')))
                if single_pass_formatting is not None:
                    if not isinstance(single_pass_formatting, Iterable):
                        to_pass = [to_pass, single_pass_formatting]
                    else:
                        single_pass_formatting.append(to_pass)
                        to_pass = single_pass_formatting
                res.extend(self.__passthrough(child, spf=to_pass))
            elif child.name == 'big':
                c = Paragraph([], formatting=Large())
                self.process(c, child)
                res.append(c)
            elif child.name in ['b', 'i', 'strong', 'em', 's', 'u']:
                to_pass = None
                if child.name in ['b', 'strong']:
                    to_pass = Bold()
                elif child.name in ['i', 'em']:
                    to_pass = Italic()
                elif child.name == 's':
                    to_pass = Strikethrough()
                elif child.name == 'u':
                    to_pass = Underline()
                if single_pass_formatting is not None:
                    if not isinstance(single_pass_formatting, Iterable):
                        to_pass = [to_pass, single_pass_formatting]
                    else:
                        single_pass_formatting.append(to_pass)
                        to_pass = single_pass_formatting
                res.extend(self.__passthrough(child, spf=to_pass))
            elif child.name == 'small':
                to_pass = Small()
                if single_pass_formatting is not None:
                    if not isinstance(single_pass_formatting, Iterable):
                        to_pass = [single_pass_formatting, to_pass]
                    else:
                        single_pass_formatting.append(to_pass)
                        to_pass = single_pass_formatting
                res.extend(self.__passthrough(child, spf=to_pass))
            elif child.name == 'pre':
                c = Container([], formatting=Monospace())
                self.process(c, child, single_pass_formatting=single_pass_formatting)
                res.append(c)
            elif child.name == 'iframe':
                src = child.attrs.get('src', '')
                if 'youtube' in src:
                    vet = VideoEmbedType.youtube
                elif 'vk.com' in src:
                    vet = VideoEmbedType.vk
                elif 'diary-media' in src:
                    vet = VideoEmbedType.diary
                elif 'coub.com' in src:
                    vet = VideoEmbedType.coub
                elif 'vimeo' in src:
                    vet = VideoEmbedType.vimeo

                if vet is not None:
                    res.append(VideoEmbed(src, style=vet, width=child.attrs.get('width'),
                                          height=child.attrs.get('height')))
                else:
                    self.errors += 1
            elif child.name == 'hr':
                res.append(LineBreak(None))
            elif child.name in ['table', 'tbody']:
                spf = []
                if child.attrs.get('style') is not None:
                    spf.append(OriginalStyle(style=child.attrs.get('style')))
                    if single_pass_formatting is not None:
                        if not isinstance(single_pass_formatting, Iterable):
                            spf.append(single_pass_formatting)
                        else:
                            spf.extend(single_pass_formatting)
                if child.attrs.get('width') is not None or child.attrs.get('height') is not None:
                    spf.append(Size(width=child.attrs.get('width'), height=child.attrs.get('height')))
                res.extend(self.__passthrough(child, spf=spf))
            elif child.name in ('td', 'th'):
                f = []
                if 'bgcolor' in child.attrs:
                    f.append(Color(color=child.attrs.get('bgcolor')))
                c = Container([], formatting=f)
                self.process(c, child)
                if c.data.__len__() == 0:
                    continue
                res.append(c)
            elif child.name == 'tr':
                c = Container([], formatting=Display(display='row'))
                self.process(c, child)
                if c.data.__len__() == 0:
                    continue
                res.append(c)
            elif child.name in ['form', 'label']:
                res.extend(self.__passthrough(child))
            elif child.name == 'input':
                typ = child.attrs.get('type', '')
                gtyp = None
                if typ == 'radio':
                    gtyp = GlyphType.circle
                elif typ == 'checkbox':
                    gtyp = GlyphType.square
                elif typ == 'hidden':
                    continue
                if gtyp is not None:
                    res.append(Glyph(gtyp))
                elif typ == 'text':
                    res.append(Text(child.attrs.get('value', '')))
                elif typ in ['input', 'submit', 'button']:
                    res.append(Surrounded(child.attrs.get('value'), left='[', right=']'))
                else:
                    self.errors += 1
                    continue
            elif child.name == 'center':
                if single_pass_formatting is not None:
                    if isinstance(single_pass_formatting, Iterable):
                        single_pass_formatting.append(Align(position='center'))
                    else:
                        single_pass_formatting = [single_pass_formatting, Align(position='center')]
                res.extend(self.__passthrough(child, spf=single_pass_formatting))
            elif child.name == 'map':
                continue
            else:
                self.errors += 1

            if hasattr(child, 'attrs') and child.attrs.get('style') is not None:
                if not self.extended:
                    res[-1].formatting.append(OriginalStyle(style=child.attrs.get('style')))

            if single_pass_formatting is not None and not self.extended:
                if not isinstance(single_pass_formatting, Iterable):
                    single_pass_formatting = [single_pass_formatting]

                res[-1].formatting.extend(single_pass_formatting)

            # https://dragons-diary.diary.ru/p33363042_soctest.htm <-- wow, shit.
        data.data = res
