from blog import Page, PageBody
from blog.data import *
from blog.format import *
from blog.model import *
from pathlib import Path
from typing import Callable


class Render:
    def __init__(self, image_path_prepend=None):
        self.global_counter = 0
        self.image_path_prepend = image_path_prepend

    def render(self, page: Page, page_body: PageBody) -> str:
        pass


SIMPLE_SPOILER_FUNC = """
function {func}() {{ 
    if (document.getElementById('{one}').style.display == 'none') {{ document.getElementById('{one}').style.display = 'block' }} else {{ document.getElementById('{one}').style.display = 'none'; }}
    if (document.getElementById('{two}').style.display == 'block') {{ document.getElementById('{two}').style.display = 'none' }} else {{ document.getElementById('{two}').style.display = 'block'; }} 
}}
"""


class HTMLGenerator(Render):


    tags = {
        Container: 'div',
        Text: 'span',
        Surrounded: 'span',
        URL: 'a',
        Image: 'img',
        NewLine: 'br',
        Glyph: 'g',
        Paragraph: 'p',
        LineBreak: 'hr',
        List: 'ul',
        ListElement: 'li',
        Header: lambda h: f'h{h.size}',
        SectionBreak: 'hr'
    }

    def image_attrs(self, dt):
        src = dt.data
        if self.image_path_prepend is not None:
            src = str(Path(self.image_path_prepend).joinpath(Path(src)))
        ret = f' src="{src}" alt="{dt.alt}" '
        if dt.width is not None:
            ret += f'width="{dt.width}" '
        if dt.height is not None:
            ret += f'height="{dt.height}" '
        return ret

    def video_embed(self, dt):
        if dt.style != VideoEmbedType.local:
            text = '<iframe'
            if dt.width is not None:
                text += f' width="{dt.width}"'
            if dt.height is not None:
                text += f' height="{dt.height}"'
            text += f' src="{dt.data}"  frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
        return text

    def render(self, page, page_body):
        body = self.__render(page_body.body)
        return f'<h1>{page.title}</h1>' \
               f'{body}'

    def display(self, st):
        dsp = 'display: '
        if st.display == 'row':
            dsp += 'flex'
        else:
            dsp += st.display
        return dsp + '; '

    def size(self, st):
        ret = ''
        if st.width is not None:
            ret += f'width: {st.width}; '
        if st.height is not None:
            ret += f'height: {st.height}; '
        return ret

    def margin(self, st):
        ret = ''
        if st.left is not None:
            ret += f'margin-left: {st.left}; '
        if st.right is not None:
            ret += f'margin-right: {st.right}; '
        if st.top is not None:
            ret += f'margin-top: {st.top}; '
        if st.bottom is not None:
            ret += f'margin-bottom: {st.bottom}; '
        return ret

    def __render(self, data: Data) -> str:
        preprocessors = {
            URL: lambda dt: f' href="{dt.href}" tooltip="{dt.tooltip}" ',  # todo: none tooltips.
            Image: self.image_attrs
        }

        processors = {
            Glyph: lambda dt: dt.data.value,
            Surrounded: lambda dt: f'{dt.left}{dt.data}{dt.right if dt.right is not None else dt.left}',
            Image: lambda dt: '',
            NewLine: lambda dt: '',
            VideoEmbed: self.video_embed
        }

        styles = {
            Align: lambda st: f'float: {st.position}; ' if st.position in ['left',
                                                                           'right'] else f' text-align: center; ',
            Italic: lambda st: f'font-style: italic; ',
            Bold: lambda st: f'font-weight: bold; ',
            Strikethrough: lambda st: f'text-decoration: line-through; ',
            Underline: lambda st: f'text-decoration: underline; ',
            Indent: lambda st: f'padding-left: {30 * st.steps}px; ',
            Display: self.display,
            Monospace: lambda st: f'font-family: MONOSPACE; white-space: pre; ',
            Size: self.size,
            Small: lambda st: f'font-size: smaller; ',
            Large: lambda st: f'font-size: larger; ',
            Muted: lambda st: f'color: #D0B2AA; ',
            OriginalStyle: lambda st: f' {st.style} ',
            Color: lambda st: f' {"background" if data.CONTAINER else "color"}: {st.color}; ',
            Margin: self.margin
        }

        style = ""
        for fmt in data.formatting:
            try:
                style += styles.get(fmt.__class__)(fmt)
            except TypeError:
                print(f'Failed on {fmt}')
                raise

        open_tag = ''
        close_tag = ''

        if data.__class__ in self.tags:
            tag = self.tags.get(data.__class__)

            if isinstance(tag, Callable):
                tag = tag(data)

            open_tag = f'<{tag}'
            processor = preprocessors.get(data.__class__)
            if processor is not None:
                open_tag += processor(data)

            if style != '':
                open_tag += f" style=\"{style}\""

            open_tag += '>'
            close_tag = f'</{tag}>'
        if data.__class__ == Spoiler:
            inner = ''.join([self.__render(q) for q in data.data])
            link = self.__render(data.spoiler_data)
            ref = f'spoilref{self.global_counter}'
            ref2 = f'spoilref2{self.global_counter}'
            fname = f'spoilf{self.global_counter}'
            f = SIMPLE_SPOILER_FUNC.format(one=ref, two=ref2, func=fname)
            self.global_counter += 1
            return f'<script>' \
                   f'{f}' \
                   f'</script>' \
                   f'<a href="#" id="{ref}" onclick="{fname}()">{link}</a>' \
                   f'<spoil id="{ref2}" ondblclick="{fname}()" style="display: none;">{inner}</spoil>'

        if (processor := processors.get(data.__class__)) is not None:
            inner = processor(data)
        elif data.CONTAINER:
            inner = ''.join([self.__render(q) for q in data.data])
        else:
            inner = str(data.data) if data.data is not None else ''

        if inner == '':
            ret = open_tag[:-1] + '/>'
        else:
            ret = open_tag + inner + close_tag

        return ret


class TailwindRender(Render):
    def render(self, page: Page, page_body: PageBody) -> str:
        """
        Renders only internal content.
        :param page:
        :param page_body:
        :return:
        """
        return self.__render(page_body.body)

    def __render(self, data: Data):
        if data is None:
            return ''

        ref = {
            NewLine: 'br',
            LineBreak: 'hr',
            Container: 'div',
            Paragraph: 'p',
            Spoiler: self.spoiler,
            Text: 'span',
            Surrounded: self.surrounded,
            List: 'ul',
            ListElement: 'li',
            Header: self.header,
            URL: self.url,
            VideoEmbed: self.media,
            Image: self.image,
            Glyph: self.glyph,
            SectionBreak: 'hr',
            str: lambda x: x,
            list: lambda l: ''.join([self.__render(q) for q in l])
        }
        proc = ref.get(data.__class__)
        if isinstance(proc, str):
            return self.generic_render(proc, data)
        else:
            assert isinstance(proc, Callable), 'Processor is neither tag nor function.'
            return proc(data)

    def __format(self, data):
        """
        Returns list of tailwind css classes and style overrides to use
        :param data: Data to get formatting from
        :return:
        """
        ref = {
            Italic: (False, 'italic'),
            Bold: (False, 'font-bold'),
            Strikethrough: (True, 'text-decoration: line-through'),
            Underline: (True, 'text-decoration: underline'),
            Color: self.color,  # use style tag instead of classes
            Align: self.align,
            Monospace: (True, 'font-family: monospace'),
            Indent: lambda dt, st: (True, f'padding-left: {30 * st.steps}px'),
            Display: self.display,
            Small: (True, 'font-size: small'),
            Large: (False, 'text-lg'),
            Muted: (False, 'text-gray-500'),
            OriginalStyle: lambda dt, st: (True, st.style),
            Size: self.size,
            Margin: self.margin
        }
        cl = []
        st = []

        for fmt in data.formatting:
            fr = ref.get(fmt.__class__)
            if isinstance(fr, Callable):
                fr = fr(data, fmt)
            [cl, st][fr[0]].append(fr[1])
        return ' '.join(cl), '; '.join(st)

    def generic_render(self, tag, data):
        cl, st = self.__format(data)
        inner = self.__render(data.data)
        return f'<{tag} class="{cl}" style="{st}">{inner}</{tag}>' if inner is not None and inner != '' else \
               f'<{tag} class="{cl}" style="{st}"/>'

    def color(self, data, fmt):
        return True, f'{"background" if data.CONTAINER else "color"}: {fmt.color}'

    def align(self, data, fmt):
        if data.CONTAINER:
            pos = 'flex '
            if fmt.position == 'left':
                pos += 'justiry-start'
            elif fmt.position == 'right':
                pos += 'justify-end'
            else:
                pos += 'justify-center'
            return False, pos
        else:
            if fmt.position == 'left':
                return False, 'text-left'
            elif fmt.position == 'right':
                return True, 'text-align: right'
            else:
                return False, 'text-center'

    def size(self, data, fmt):
        fm = []
        if fmt.width is not None:
            fm.append(f'width: {fmt.width}')
        if fmt.height is not None:
            fm.append(f'height: {fmt.height}')
        return True, '; '.join(fm)


    def display(self, data, fmt):
        if fmt.display == 'row':
            return False, 'flex flex-row'
        else:
            return True, f'display: {fmt.display}'

    def margin(self, data, fmt):
        ret = []
        if fmt.left is not None:
            ret.append(f'margin-left: {fmt.left}')
        if fmt.right is not None:
            ret.append(f'margin-right: {fmt.right}')
        if fmt.top is not None:
            ret.append(f'margin-top: {fmt.top}')
        if fmt.bottom is not None:
            ret.append(f'margin-bottom: {fmt.bottom}')
        return True, '; '.join(ret)

    def spoiler(self, data):
        cl, st = self.__format(data)
        name = 'n'+hex(id(data))[2:]
        f = SIMPLE_SPOILER_FUNC.format(one=f'{name}url', two=f'{name}container', func=f'{name}func')
        # todo mark that this is a spoiler.
        return f'<script>' \
               f'{f}' \
               f'</script>' \
               f'<a href="#" id="{name}url" onclick="{name}func()">{self.__render(data.spoiler_data)}</a>' \
               f'<spoil id="{name}container" ondblclick="{name}func()" style="display: none; {st}" class="{cl}">' \
               f'{self.__render(data.data)}' \
               f'</spoil>'

    def surrounded(self, data):
        cl, st = self.__format(data)
        return f'<span style="{st}" class="{cl}">{data.left}{self.__render(data.data)}' \
               f'{data.right if data.right is not None else data.left}</span>'

    def header(self, data):
        cl, st = self.__format(data)
        htag = f'h{data.size}'
        return f'<{htag} style="{st}" class="{cl}">{self.__render(data.data)}</{htag}>'

    def url(self, data):
        cl, st = self.__format(data)
        href = data.href
        ex = ''
        if data.tooltip is not None:
            ex = f'<span class="tooltip-text bg-gray-700 text-white text-sm rounded p-2">{data.tooltip}</span>'
            cl += ' tooltip'
        return f'<a href="{href}" style="{st}" class="{cl}">{ex}{self.__render(data.data)}</a>'

    def media(self, data):
        cl, st = self.__format(data)
        if data.style != VideoEmbedType.local:
            text = '<iframe'
            if data.width is not None:
                text += f' width="{data.width}"'
            if data.height is not None:
                text += f' height="{data.height}"'
            text += f' src="{data.data}" style="{st}" class="{cl}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
        return text

    def image(self, data):
        cl, st = self.__format(data)
        src = data.data
        if self.image_path_prepend is not None and not src.startswith('http'):
            src = str(Path(self.image_path_prepend).joinpath(Path(src)))
        ret = f'<img src="{src}" alt="{data.alt}" class="{cl}" style="{st}" '
        if data.width is not None:
            ret += f'width="{data.width}" '
        if data.height is not None:
            ret += f'height="{data.height}" '
        ret += '/>'
        return ret

    def glyph(self, data):
        # todo: modify glyphs to look cooler and stuff.
        return data.data.value
