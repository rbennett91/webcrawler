import multiprocessing
import threading
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class BaseCrawler(object):
    def run(self):
        while self.get_url_count() < self.min_urls:
            url_to_scrape = self.get_next_url()
            if url_to_scrape:
                new_urls = self.scrape_url(url_to_scrape)
                if new_urls:
                    self.add_urls(url_to_scrape, new_urls)

    def get_url_count(self):
        raise NotImplementedError

    def get_next_url(self):
        raise NotImplementedError

    def add_urls(self):
        raise NotImplementedError

    def scrape_url(self, url):
        try:
            response = requests.get(url)
        except Exception:
            return ()

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.findAll('a')
        clean_urls = self.sanitize_urls(url, links)

        return clean_urls

    def sanitize_urls(self, base_url, urls_to_sanitize):
        clean_urls = set()

        for url in urls_to_sanitize:
            href = url.get('href')
            if not self.url_has_http_scheme(href):
                continue

            if self.is_absolute_url(href):
                absolute_url = href
            else:
                absolute_url = self.make_absolute_url(base_url, href)

            clean_urls.add(absolute_url)

        return clean_urls

    def is_absolute_url(self, url):
        return bool(urlparse(url).netloc)

    def make_absolute_url(self, base_url, relative_url):
        return urljoin(base_url, relative_url)

    def url_has_http_scheme(self, url):
        return urlparse(url).scheme in ('http', 'https')


class Crawler1(BaseCrawler):
    def __init__(self, kwargs={}):
        super(Crawler1, self).__init__(kwargs=kwargs)
        self.redis_connection = kwargs.get('redis_connection')
        self.min_urls = kwargs.get('min_urls')
        self.url_position_lock = kwargs.get('url_position_lock')
        self.url_insertion_lock = kwargs.get('url_insertion_lock')

    def get_next_url(self):
        with self.url_position_lock:
            try:
                next_url_position = self.redis_connection.get(
                    'c1_next_url_position'
                )
                next_url = self.redis_connection.zrange(
                    'c1_sorted_url_set',
                    next_url_position,
                    next_url_position,
                )[0]

                self.set_next_url()
                return next_url

            except IndexError:
                return None

    def set_next_url(self):
        next_url_position = int(
            self.redis_connection.get('c1_next_url_position')
        )
        next_url_position += 1
        self.redis_connection.set('c1_next_url_position', next_url_position)

    def get_url_count(self):
        return self.redis_connection.zcard('c1_sorted_url_set')

    def add_urls(self, base_url, new_urls):
        with self.url_insertion_lock:
            for url in new_urls:
                next_position = self.get_url_count()

                zscore = self.redis_connection.zscore(
                    'c1_sorted_url_set',
                    url
                )
                if zscore is None:
                    self.redis_connection.zadd(
                        'c1_sorted_url_set',
                        next_position,
                        url
                    )


class Crawler2(BaseCrawler):
    def __init__(self, kwargs={}):
        super(Crawler2, self).__init__(kwargs=kwargs)
        self.redis_connection = kwargs.get('redis_connection')
        self.min_urls = kwargs.get('min_urls')

    def get_next_url(self):
        rlist, url = self.redis_connection.brpop('c2_url_queue_list')
        return url

    def get_url_count(self):
        return self.redis_connection.scard('c2_url_set')

    def add_urls(self, base_url, new_urls):
        self.redis_connection.sadd('c2_url_set', base_url)

        for url in new_urls:
            if self.redis_connection.sadd('c2_url_set', url):
                self.redis_connection.lpush('c2_url_queue_list', url)


class MyThreadCrawler1(Crawler1, threading.Thread):
    def __init__(self, kwargs={}):
        super(MyThreadCrawler1, self).__init__(kwargs=kwargs)


class MyProcessCrawler1(Crawler1, multiprocessing.Process):
    def __init__(self, kwargs={}):
        super(MyProcessCrawler1, self).__init__(kwargs=kwargs)


class MyThreadCrawler2(Crawler2, threading.Thread):
    def __init__(self, kwargs={}):
        super(MyThreadCrawler2, self).__init__(kwargs=kwargs)


class MyProcessCrawler2(Crawler2, multiprocessing.Process):
    def __init__(self, kwargs={}):
        super(MyProcessCrawler2, self).__init__(kwargs=kwargs)
