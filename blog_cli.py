

from blog import Blog
from blog.render import HTMLGenerator
import argparse

p = argparse.ArgumentParser()
p.add_argument('--command', '-c', choices=['init', 'rename', 'health', 'show', 'render', 'retag'], help='Action to do')
p.add_argument('--local_folder', '-l', default='data/blog', help='Local folder to work in and try to find blog.pcl')
p.add_argument('--target', '-t', default=None, help='Target of the command')
p.add_argument('params', metavar=argparse.REMAINDER, nargs='*')

if __name__ == '__main__':
    args = p.parse_args()

    if args.command == 'init':
        Blog.initialize_empty(args.local_folder)

    blog = Blog(None, local_folder=args.local_folder)

    if args.command == 'health':
        print(f'Blog has loaded')
        print(blog.get_health())
        random_page = list(blog._Blog__meta.keys())[0]
        page = blog.get_page_by_id(random_page)
        print(page)
        body = blog.get_page_body(page)
        print(body)
        print(body.body)

    if args.command == 'render':
        print(f'Rendering {args.target}')
        if args.target == 'random':
            page = blog.get_random_page()
        else:
            page = blog.get_page_by_id(args.target)
        body = blog.get_page_body(page)
        gen = HTMLGenerator()
        print(page.original_url)
        with open('temp/page.html', 'w', encoding='utf-8') as f:
            f.write(gen.render(page, body))
        for img in body.images:
            with open(f'temp/{img}', 'wb') as f:
                f.write(body.images[img])
        print('Done')

    if args.command == 'show':
        if args.target == 'tags':
            print(blog.get_all_tags())
        else:
            page = blog.get_page_by_id(args.target)
            print(page)

    if args.command == 'retag':
        tag1, tag2 = args.params
        blog.replace_tag(tag1, tag2)
