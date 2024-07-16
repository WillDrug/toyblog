from .model import Configurable, Missing


class Format(Configurable):
    pass


class Italic(Format): pass


class Bold(Format): pass

class Strikethrough(Format): pass

class Underline(Format): pass

class Color(Format):
    EXPECT_CONFIG = {
        'color': Missing()
    }

class Align(Format):
    EXPECT_CONFIG = {
        'position': Missing()
    }

class Monospace(Format):  pass

class Indent(Format):
    EXPECT_CONFIG = {
        'steps': 0
    }


class Display(Format):
    EXPECT_CONFIG = {
        'display': 'block'
    }

class Small(Format): pass

class Large(Format): pass

class Muted(Format): pass

class OriginalStyle(Format):
    EXPECT_CONFIG = {
        'style': Missing()
    }

class Size(Format):
    EXPECT_CONFIG = {
        'width': None,
        'height': None
    }

class Margin(Format):
    EXPECT_CONFIG = {
        'left': None,
        'right': None,
        'top': None,
        'bottom': None
    }