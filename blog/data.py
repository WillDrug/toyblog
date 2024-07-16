from .format import *
from .model import Configurable, GlyphType
from typing import Iterable


class Data(Configurable):
    CONTAINER = False

    def __init__(self, data, formatting: Format | Iterable[Format] = tuple(), **kwargs):
        super().__init__(**kwargs)
        if formatting is None:
            formatting = tuple()

        if not isinstance(formatting, Iterable):
            formatting = (formatting,)

        self.formatting = list(formatting)
        self.data = data
        self.validate()

    def validate(self):
        """
        Override for specific types or keep generic markers.
        :return: None; Raises an exception on a problem.
        """
        if self.CONTAINER:
            if not isinstance(self.data, Iterable):
                raise AttributeError(f'{self.__class__.__name__} is designated as a container but got {self.data}')

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.data})>'


class NewLine(Data):
    def validate(self):
        if self.data is not None:
            raise AttributeError(f'Newline does not accept data')


class LineBreak(NewLine): pass


class Container(Data):
    CONTAINER = True


class Paragraph(Container):
    pass


class Spoiler(Container):
    EXPECT_CONFIG = {
        'spoiler_data': None
    }


class Text(Data): pass

class Surrounded(Text):
    EXPECT_CONFIG = {
        'left': '',
        'right': None
    }

class List(Data):
    CONTAINER = True
    EXPECT_CONFIG = {
        'list_type': GlyphType.circle  # type or glyph
    }

class ListElement(Data):
    CONTAINER = True

class Header(Data):
    CONTAINER = True
    EXPECT_CONFIG = {
        'size': 1
    }


class URL(Container):
    EXPECT_CONFIG = {
        'href': None,
        'tooltip': None
    }


class VideoEmbed(Data):
    EXPECT_CONFIG = {
        'style': None,
        'width': None,
        'height': None
    }


class Image(Data):
    EXPECT_CONFIG = {
        'width': None,
        'height': None,
        'alt': None
    }


class Glyph(Data):
    def validate(self):
        if isinstance(self.data, str):
            self.data = GlyphType(self.data)
        if not isinstance(self.data, GlyphType):
            raise AttributeError(f'Glyph {self.data} was not found.')

class SectionBreak(Data):  pass


class Banner(Data):  pass