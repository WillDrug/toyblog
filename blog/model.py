from enum import Enum

class Missing: pass


class Configurable:
    EXPECT_CONFIG = {}

    def __init__(self, **kwargs):
        for k in self.EXPECT_CONFIG:
            val = kwargs.get(k, self.EXPECT_CONFIG[k])
            if isinstance(val, Missing):
                raise AttributeError(f'{self.__class__.__name__} expected {k} parameter to be created')
            setattr(self, k, val)


class GlyphType(Enum):
    diary_dog = '@'
    circle = '*'
    square = '[]'
    button = '[]'

class VideoEmbedType(Enum):
    youtube = 'youtube'
    vk = 'vk'
    diary = 'diary'
    coub = 'coub'
    vimeo = 'vimeo'
    local = 'local'