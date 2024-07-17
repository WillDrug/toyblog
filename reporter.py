

from os import getenv
from blog_web import app, tc
if not getenv('LOCAL'):
    print(f'Starting reporter.')
    tc.discover.set_params(tc.name, 'Little Blog', 'An archive of old and a storage for new', tags=['Personal', 'Article'])
    tc.discover.start_reporting()

if __name__ == '__main__':
    # used only for debugging with LOCAL expected.
    app.run('0.0.0.0', '8888', debug=True)