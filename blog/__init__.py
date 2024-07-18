"""
1) Provide data structure
2) Provide data representation
3) Reference images only by filename, contain a list of glyphs
"""

from .format import *
from .data import *
from datetime import date
import pickle
from random import choice
from pathlib import Path
from itertools import chain
import os


# import storage abstraction


class Blog:  # this should hold pages, index and do search
    domain = 'blog'
    blog_file = 'blog.pcl'

    def get_data_from_file(self, file_name, folder=None, resync=False):
        if self.__drive is not None:
            # no processing. synced file will save itself as a pickle of a binary on it's own
            # then load via pickle here.
            f = self.__drive.get_synced_file(self.domain, file_name, process_function=lambda data: data,
                                             filename=f'{self.local_folder}/{file_name}', folder=folder)
            if resync:
                f.sync()
            data = f.data
        else:
            if folder == self.domain:  # local functionality has local as root folder instead of domain.
                folder = None
            if folder is None:
                p = f'{self.local_folder}/{file_name}'
            else:
                p = f'{self.local_folder}/{folder}/{file_name}'
            with open(p, 'rb') as f:
                data = f.read()
        return pickle.loads(data)

    def save_page_body(self, body, page_type, page_id):
        Path(f'{self.local_folder}/{page_type}').mkdir(parents=True, exist_ok=True)
        with open(f'{self.local_folder}/{page_type}/{page_id}.pcl', 'wb') as f:
            f.write(pickle.dumps(body))
        return f'{page_id}.pcl'

    def __init__(self, drive=None, local_folder=None):
        if local_folder is None:
            local_folder = os.getenv('BLOG_LOCAL_FOLDER', 'data')  # used for master location *OR* temp local location
        self.local_folder = local_folder
        self.__drive = drive  # Drive() or DriveMock()
        if self.__drive is not None:
            # todo: fix DriveMock() directories and shit to work with this.
            self.__drive.add_directory(self.domain)  # this should contain body files. equivalent to local_folder.

        self.__meta = self.get_data_from_file(self.blog_file, folder=self.domain)  # dict of Page objects.

        if self.__drive is not None:
            # add all possible subfolders within main blog
            for folder in self.get_subfolders():
                self.__drive.add_directory(folder, parent=self.domain, )
        # meta has Page objects.
        # meta file is loaded upon init once and updated via request (sync can be handled by web, re-load here)
        # page files are loaded on-demand

    def get_subfolders(self):
        """
        :return: list of strings signifying page-type from pages.
        """
        return list(set([q.page_type for q in self.__meta.values()]))

    def subfolder_size(self, subfolder):
        return len([q for q in self.__meta.values() if q.page_type == subfolder])

    def get_health(self):  # to add: orphans, etc.
        return {
            'subfolders': self.get_subfolders(),
            'total_pages': self.__meta.__len__()
        }

    def add_page(self, created_at: date, page_id, body: "Data",
                 page_type: str, tags=None, visible=False,
                 title: str = '', original_url: str = None, image_data=None, force=False):
        # page id should be editable for future reference, so, not used anywhere in permanent, only decompositions.
        if self.__drive is not None:
            raise RuntimeError(f'Editing is not permitted during operation. Run via CLI instead.')
        if page_id in [q.page_id for q in self.__meta.values()]:
            if force:
                print(f'Overwriting {page_id}!')
            else:
                raise AttributeError(f'Page {page_id} already exists.')
        b = PageBody(body, image_data=image_data)
        self.save_page_body(b, page_type, page_id)
        p = Page(created_at, page_id, page_type, tags=tags, visible=visible, title=title,
                 original_url=original_url)
        self.__meta[page_id] = p
        # self.save()

    def get_latest(self, num, visible=True):
        return sorted([q for q in self.__meta.values() if q.visible or visible], key=lambda page: page.created_at, reverse=True)[:num]

    def search_pages(self, tags=None, title=None, date_from=None, date_to=None, visible=True):
        ret = []
        for page in self.__meta.values():
            if not page.visible and not visible:
                continue
            if tags is not None:
                to_break = False
                for tag in tags:
                    if tag not in page.tags:
                        to_break = True
                if to_break:
                    continue
            if title is not None:
                if title.lower() not in page.title.lower():  # todo better vague search
                    continue
            if date_from is not None:
                if page.created_at < date_from:
                    continue
            if date_to is not None:
                if page.created_at > date_to:
                    continue
            ret.append(page)
        ret = sorted(ret, key=lambda x: x.created_at, reverse=True)
        return ret

    def clean_files(self):
        """
        todo: make this function crawl through page body files and find those which are not used in the meta.
        then delete them.
        :return:
        """
        pass

    def save(self):
        if self.__drive is not None:
            raise RuntimeError(f'Editing is not permitted during operation. Run via CLI instead.')
        data = pickle.dumps(self.__meta)
        with open(f'{self.local_folder}/{self.blog_file}', 'wb') as f:
            f.write(data)

    def replace_tag(self, tag1, tag2):
        for page in self.__meta.values():
            if tag1 in page.tags:
                page.tags.remove(tag1)
                page.tags.append(tag2)
                print(f'Retagged {page.page_id}')
        self.save()

    def change_page_id(self, old_id, new_id):
        """ Operates on self.page_file.
        :param old_id: Old filename
        :param new_id: New filename
        :return:
        """
        if self.__drive is not None:
            raise RuntimeError(f'Editing is not permitted during operation. Run via CLI instead.')
        page = self.get_page_by_id(old_id)
        # write new
        b = self.get_page_body(page)
        self.save_page_body(b, page.page_type, new_id)
        page.page_id = new_id
        # delete old
        file_to_rem = Path(f'{self.local_folder}/{page.page_type}/{page.page_id}.pcl')
        file_to_rem.unlink()

    def get_page_body(self, page, resync=False):
        return self.get_data_from_file(f'{page.page_id}.pcl', folder=page.page_type, resync=resync)

    def get_page_by_id(self, page_id):
        return next((q for q in self.__meta.values() if q.page_id == page_id), None)

    def get_pages_by_tag(self, tag):
        return [q for q in self.__meta.values() if tag in q.tags]

    def get_random_page(self):
        return choice(list(self.__meta.values()))

    def get_all_tags(self, visible=True):
        return list(set(chain(*[q.tags for q in self.__meta.values() if q.visible or visible])))

    def get_all_tags_with_count(self):
        tags = {}
        for page in self.__meta.values():
            for tag in page.tags:
                if tag not in tags:
                    tags[tag] = 0
                tags[tag] += 1
        return tags

    @classmethod
    def initialize_empty(cls, folder):
        with open(f'{folder}/{cls.blog_file}', 'wb') as f:
            f.write(pickle.dumps({}))

    def get_dates(self):
        ret = {}
        for page in self.__meta.values():
            dt = str(page.created_at)
            if dt not in ret:
                ret[dt] = 0
            ret[dt] += 1
        return ret


class PageBody:
    def __init__(self, body, image_data=None):
        if image_data is None:
            image_data = {}
        self.body = body  # body images reference
        self.images = image_data


class Page:
    def __init__(self, created_at, page_id, page_type, tags=None, title='',
                 visible=True, original_url=''):
        if tags is None:
            tags = []
        self.title = title or ''
        self.created_at = created_at
        self.page_id = page_id
        self.page_type = page_type
        self.tags = tags
        self.visible = visible
        self.original_url = original_url

    def __str__(self):
        return f'<Page({self.title} [{", ".join(self.tags)}])>'
