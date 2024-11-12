

from os import getenv
from blog_web import app, tc


def on_starting(server):
    if not getenv('LOCAL'):
        print(f'Starting reporter.')
        tc.discover.set_params(tc.name, 'Little Blog', 'An archive of old and a storage for new',
                               tags=['Personal', 'Article'])
        tc.discover.start_reporting()
