import json
import multiprocessing
import threading
import time
from urllib.parse import urljoin, urlparse

import redis
import requests
from bs4 import BeautifulSoup


def load_config():
    with open('./config.json') as config_file:
        return json.load(config_file)


def get_redis_connection(config):
    return redis.StrictRedis(
        host=config['redis']['host'],
        port=config['redis']['port'],
        db=config['redis']['db'],
        decode_responses=config['redis']['decode_responses']
    )


def initialize_redis_db(redis_connection, root_url):
    redis_connection.flushdb()
    redis_connection.zadd('sorted_url_set', 0, root_url)
    redis_connection.set('next_url_position', 0)


class MyBaseCrawler(object):
    def __init__(self, kwargs={}):
        super(MyBaseCrawler, self).__init__(kwargs=kwargs)
        self.redis_connection = kwargs.get('redis_connection')
        self.max_urls = kwargs.get('max_urls')
        self.url_position_lock = kwargs.get('url_position_lock')
        self.url_insertion_lock = kwargs.get('url_insertion_lock')

    def run(self):
        while True:
            if self.get_url_count() >= self.max_urls:
                break

            url_to_scrape = self.get_next_url()
            if url_to_scrape:
                new_urls = self.scrape_url(url_to_scrape)
                if new_urls:
                    self.add_urls(url_to_scrape, new_urls)

    def get_next_url(self):
        with self.url_position_lock:
            try:
                next_url_position = self.redis_connection.get('next_url_position')
                next_url = self.redis_connection.zrange(
                    'sorted_url_set',
                    next_url_position,
                    next_url_position,
                )[0]
            except IndexError:
                return None

            self.set_next_url()
            return next_url

    def set_next_url(self):
        next_url_position = int(self.redis_connection.get('next_url_position'))
        next_url_position += 1
        self.redis_connection.set('next_url_position', next_url_position)

    def get_url_count(self):
        return self.redis_connection.zcard('sorted_url_set')

    def scrape_url(self, url):
        try:
            response = requests.get(url)
        except Exception:
            return ()

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.findAll('a')

        return links

    def add_urls(self, base_url, new_urls):
        with self.url_insertion_lock:
            for url in new_urls:
                next_position = self.get_url_count()
                if next_position >= self.max_urls:
                    return

                href = url.get('href')
                if not self.url_has_http_scheme(href):
                    continue

                if self.is_absolute_url(href):
                    absolute_url = href
                else:
                    absolute_url = self.make_absolute_url(base_url, href)

                zscore = self.redis_connection.zscore(
                    'sorted_url_set',
                    absolute_url
                )
                if zscore is None:
                    self.redis_connection.zadd(
                        'sorted_url_set',
                        next_position,
                        absolute_url
                    )

    def is_absolute_url(self, url):
        return bool(urlparse(url).netloc)

    def make_absolute_url(self, base_url, relative_url):
        return urljoin(base_url, relative_url)

    def url_has_http_scheme(self, url):
        return urlparse(url).scheme in ('http', 'https')


class MyThreadCrawler(MyBaseCrawler, threading.Thread):
    def __init__(self, kwargs={}):
        super(MyThreadCrawler, self).__init__(kwargs=kwargs)


class MyProcessCrawler(MyBaseCrawler, multiprocessing.Process):
    def __init__(self, kwargs={}):
        super(MyProcessCrawler, self).__init__(kwargs=kwargs)


def main():
    print('-------------------------')
    print("configuring...")

    config = load_config()
    redis_connection = get_redis_connection(config)
    initialize_redis_db(redis_connection, config['root_url'])

    url_position_lock = threading.Semaphore(value=1)
    url_insertion_lock = threading.Semaphore(value=1)

    #  url_position_lock = multiprocessing.Semaphore(value=1)
    #  url_insertion_lock = multiprocessing.Semaphore(value=1)

    kwargs = {
        'redis_connection': redis_connection,
        'max_urls': config['max_urls'],
        'url_position_lock': url_position_lock,
        'url_insertion_lock': url_insertion_lock,
    }

    worker1 = MyThreadCrawler(kwargs=kwargs)
    worker2 = MyThreadCrawler(kwargs=kwargs)

    #  worker1 = MyProcessCrawler(kwargs=kwargs)
    #  worker2 = MyProcessCrawler(kwargs=kwargs)

    print("starting to scrape...")
    t0 = time.time()

    worker1.start()
    worker2.start()

    worker1.join()
    worker2.join()

    t1 = time.time()
    print("finished scraping...")
    elapsed_time = round(t1 - t0, 2)
    print("elapsed scraping time: {} seconds".format(elapsed_time))
    print('-------------------------')


if __name__ == '__main__':
    main()
