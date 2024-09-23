

from os import getenv
from blog_web import app, tc

if __name__ == '__main__':
    if not getenv('LOCAL'):
        print(f'Starting reporter.')
        tc.discover.set_params(tc.name, 'Little Blog', 'An archive of old and a storage for new',
                               tags=['Personal', 'Article'])
        tc.discover.start_reporting()