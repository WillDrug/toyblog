from blog import Blog, Page, PageBody
from crawler import Crawler, DiaryLoader
from blog.render import HTMLGenerator
from tqdm import tqdm

LOADERS = {
    'diary': DiaryLoader
}

import argparse

p = argparse.ArgumentParser()
p.add_argument('--command', '-c', choices=['crawl', 'add_listing', 'crawl_single',
                                           'load', 'parse', 'show', 'offload', 'fix',
                                           'render', 'clear', 'imgref'], help='Action to do')
p.add_argument('--loader', '-l', help='Which loader to use', choices=list(LOADERS.keys()))
p.add_argument('--target', '-t', default=None, help='Which page to load, crawl or parse. Empty assumed all')
p.add_argument('--auth', '-a', default=None, help='Authentication string for the loader used (consult readme)')
p.add_argument('--force', '-f', default=False, help='Forces crawl commands to overwrite data')
p.add_argument('--output', '-o', default=None, help='Output target')

if __name__ == '__main__':
    args = p.parse_args()
    if args.loader is None:
        print(f'Supply loader type. Supported: {list(LOADERS.keys())}')
        print('It will remember info and auth.')
        exit()

    c = Crawler(LOADERS.get(args.loader), auth=args.auth)


    if args.command == 'crawl':
        print('Crawling...')
        err = c.crawl(base_url=args.target, force=args.force)
        if err is not None:
            print(err)
        print(f'Done. Loaded {c.get_all_pages().__len__()} pages.')
    elif args.command == 'crawl_single':
        c.crawl(single_listing=args.target, force=args.force)
        print('Crawled')
    elif args.command == 'add_listing':
        if args.target is None:
            print('Specify listing target url')
            exit()
        c.add_listing(args.target)
        print('Added listing')
    if args.command == 'load' or (args.command == 'render' and args.force == '2'):
        if args.target is None:
            print(f'Loading all page data to db')
            c.load_pages(force=args.force)
        else:
            page = c.get_page_by_url(args.target) if args.target.startswith('http') else c.get_page_by_id(args.target)
            if page is not None:
                print(f'Reloading {args.target} data')
                c.load_page(page)
            else:
                print(f'Loading {args.target}')
                c.add_page(args.target)
            c.save()
        print('Done')
    if args.command == 'imgref':
        if args.target == 'build':
            for page in c.get_all_pages():
                c.build_img_ref(page)
            c.save()
        elif args.target == 'load':
            for page in tqdm(c.get_all_pages()):
                c.load_img_ref(page, force=args.force)
            c.save()
        else:
            page = c.get_page_by_url(args.target) if args.target.startswith('http') else c.get_page_by_id(args.target)
            c.load_img_ref(page, force=args.force)

    if args.command == 'fix':
        if args.target is None:
            print('Set target. "listings" to fix urls, "8000" to fix weird 8000 problems')
        if args.target == 'listings':
            print('Fixing listings')
            c.fix_listings()
        elif args.target == '?':
            gl_cnt = 0
            fl_cnt = 0
            for page in tqdm(c.get_all_pages()):
                cnt = 0
                if '�' in page.data:
                    while '�' in page.data:
                        c.load_page(page)
                        cnt += 1
                        if cnt >= 3:
                            print(f'Failed on {page.unique_id}')
                            fl_cnt += 1
                            break
                    else:
                        gl_cnt += 1

            print(f'Fixed {gl_cnt} / {gl_cnt + fl_cnt}')
            c.save()
        elif args.target.startswith('http'):
            page = c.get_page_by_url('https://dragons-diary.diary.ru/p38563309_bred-ot-remycha.htm')
            if page is None:
                print('page not found')
                exit()
            c.load_page(page)
            c.parse_page(page)
            c.save()
        print('Done')

    if args.command == 'clear':
        if args.target == 'listings':
            c.clear_listings()
        elif args.target == 'pages':
            c.clear_pages()
        else:
            c.clear_listings()
            c.clear_pages()
        c.save()

    if args.command == 'parse' or (args.command == 'render' and args.force):
        if args.target is None:
            print('Parsing all pages')
            c.parse_pages(force=args.force)
        else:
            print(f'Re-parsing {args.target}')
            page = c.get_page_by_url(args.target) if args.target.startswith('http') else c.get_page_by_id(args.target)
            c.parse_page(page)
            print(f'Number of errors: {page.errors}')
            c.save()
        print('Done')

    if args.command == 'offload':
        print('This will later offload crawler-loader combo into blog itself.')
        if args.output is None:
            print(f'Specify --output for blog root location')

        blog = Blog(local_folder=args.output)

        if args.target is None:
            for page in tqdm(c.get_all_pages()):
                if not hasattr(page, 'offload_error'):
                    page.offload_error = False

                if not page.offload_error and not args.force:
                    continue

                if blog.get_page_by_id(page.unique_id) is not None and not args.force:
                    continue

                page.load_image_ref()
                img_ref = {page.image_ref[q].name: page.image_ref[q].data for q in page.image_ref
                           if not page.image_ref[q].error}
                created_at = page.blog_data.created_at
                page_id = page.unique_id
                body_data = c.get_blog_data_with_img_ref_names(page)
                page_type = 'diary'
                tags = page.blog_data.tags
                title = page.blog_data.title
                original_url = page.web_url
                blog.add_page(created_at, page_id, body_data, page_type, tags=tags,
                              title=title, original_url=original_url, image_data=img_ref, force=args.force)
        else:
            page = c.get_page_by_url(args.target) if args.target.startswith('http') else c.get_page_by_id(args.target)
            page.load_image_ref()
            img_ref = {page.image_ref[q].name: page.image_ref[q].data for q in page.image_ref
                       if not page.image_ref[q].error}
            created_at = page.blog_data.created_at
            page_id = page.unique_id
            body_data = c.get_blog_data_with_img_ref_names(page)
            page_type = c.loader.page_type
            tags = page.blog_data.tags
            title = page.blog_data.title
            original_url = page.web_url
            page.offload_error = False
            blog.add_page(created_at, page_id, body_data, page_type, tags=tags,
                          title=title, original_url=original_url, image_data=img_ref, force=args.force)

        blog.save()

    if args.command == 'show':
        if args.target is None:
            print('You can specify what to show with -t {loaded, parsed, errors, listings}')
        if args.target == 'listings':
            pages = c.get_all_listings()
            print(f'Uncrawled:')
            print([q for q in pages if not q.crawled])
            print(f'Total {[q for q in pages if q.crawled].__len__()}/{pages.__len__()} processed')
        if args.target == 'blog':
            blog = Blog(local_folder=args.output)
            print(f'Blog size: {blog.subfolder_size(c.loader.page_type)}; Crawler size: {len(c.get_all_pages())};')
            for page in c.get_all_pages():
                if blog.get_page_by_id(page.unique_id) is None:
                    print(f'Unsynced: {page.web_url}')
        if args.target == 'imgerr':
            images = {}
            for page in c.get_all_pages():
                page.load_image_ref()
                for image in page.image_ref:
                    if page.image_ref[image].error:
                        err = page.image_ref[image].error_message.split(':')[0]
                        if err not in images:
                            images[err] = 0
                        images[err] += 1
            print(images)

        if args.target in ['loaded', 'parsed', 'errors']:
            pages = c.get_all_pages()
            if args.target == 'loaded':
                pages = [q for q in pages if q.loaded]
            if args.target == 'parsed':
                pages = [q for q in pages if q.parsed]
            if args.target == 'errors':
                pages = [q for q in pages if q.errors > 0]
            if pages.__len__() > 20:
                print(pages[:10])
                print(f'---- {pages.__len__()-20} MORE PAGES ----')
                print(pages[-10:])
            else:
                print(pages)
        if args.target.startswith('http'):
            page = c.get_page_by_url(args.target)
            print(page.unique_id)

    if args.command == 'render':
        if args.target is None:
            print('Specify page by id or url')
            exit()
        if args.output is None:
            output = 'temp/page.html'
        else:
            output = args.output
        page = c.get_page_by_url(args.target) if args.target.startswith('http') else c.get_page_by_id(args.target)
        if page is None:
            print('Page not found')
            exit()
        print(page.web_url)
        rp = Page(page.blog_data.created_at, page.unique_id, 'diary', tags=page.blog_data.tags,
                  title=page.blog_data.title, original_url=page.web_url)

        rpb = PageBody(page.blog_data.data)
        renderer = HTMLGenerator()
        with open(output, 'w', encoding='utf-8') as f:
            f.write(renderer.render(rp, rpb))
