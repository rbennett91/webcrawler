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

    # create sorted set and counter for Crawler1 objects
    redis_connection.zadd('sorted_url_set', 0, root_url)
    redis_connection.set('next_url_position', 0)

    # create set and list for Crawler2 objects
    #  redis_connection.sadd('url_set', root_url)
    redis_connection.lpush('url_queue_list', root_url)


class MyBaseCrawler1(object):
    def __init__(self, kwargs={}):
        super(MyBaseCrawler1, self).__init__(kwargs=kwargs)
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

        return self.sanitize_urls(url, links)

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

    def add_urls(self, base_url, new_urls):
        with self.url_insertion_lock:
            for url in new_urls:
                next_position = self.get_url_count()
                if next_position >= self.max_urls:
                    return

                zscore = self.redis_connection.zscore(
                    'sorted_url_set',
                    url
                )
                if zscore is None:
                    self.redis_connection.zadd(
                        'sorted_url_set',
                        next_position,
                        url
                    )

    def is_absolute_url(self, url):
        return bool(urlparse(url).netloc)

    def make_absolute_url(self, base_url, relative_url):
        return urljoin(base_url, relative_url)

    def url_has_http_scheme(self, url):
        return urlparse(url).scheme in ('http', 'https')


class MyBaseCrawler2(object):
    def __init__(self, kwargs={}):
        super(MyBaseCrawler2, self).__init__(kwargs=kwargs)
        self.redis_connection = kwargs.get('redis_connection')
        self.max_urls = kwargs.get('max_urls')

    def run(self):
        while True:
            if self.get_url_count() >= self.max_urls:
                print("...url count is at the max, exiting")
                break

            #  print("...getting next url")
            url_to_scrape = self.get_next_url()

            if url_to_scrape:
                #  print("...scraping ", url_to_scrape)
                new_urls = self.scrape_url(url_to_scrape)
                if new_urls:
                    #  print("...got new urls ", len(new_urls))
                    self.add_urls(url_to_scrape, new_urls)

    def get_next_url(self):
        rlist, url = self.redis_connection.brpop('url_queue_list')
        return url

    def get_url_count(self):
        #  print("GETURLCOUNT ", self.redis_connection.scard('url_set'))
        return self.redis_connection.scard('url_set')

    def scrape_url(self, url):
        try:
            response = requests.get(url)
        except Exception:
            return ()

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.findAll('a')

        return self.sanitize_urls(url, links)

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

    def add_urls(self, base_url, new_urls):
        self.redis_connection.sadd('url_set', base_url)

        for url in new_urls:
            next_position = self.get_url_count()
            if next_position >= self.max_urls:
                return

            if not self.redis_connection.sismember('url_set', url):
                self.redis_connection.sadd('url_set', url)
                self.redis_connection.lpush('url_queue_list', url)

    def is_absolute_url(self, url):
        return bool(urlparse(url).netloc)

    def make_absolute_url(self, base_url, relative_url):
        return urljoin(base_url, relative_url)

    def url_has_http_scheme(self, url):
        return urlparse(url).scheme in ('http', 'https')


class MyThreadCrawler1(MyBaseCrawler1, threading.Thread):
    def __init__(self, kwargs={}):
        super(MyThreadCrawler1, self).__init__(kwargs=kwargs)


class MyProcessCrawler1(MyBaseCrawler1, multiprocessing.Process):
    def __init__(self, kwargs={}):
        super(MyProcessCrawler1, self).__init__(kwargs=kwargs)


class MyThreadCrawler2(MyBaseCrawler2, threading.Thread):
    def __init__(self, kwargs={}):
        super(MyThreadCrawler2, self).__init__(kwargs=kwargs)


class MyProcessCrawler2(MyBaseCrawler2, multiprocessing.Process):
    def __init__(self, kwargs={}):
        super(MyProcessCrawler2, self).__init__(kwargs=kwargs)


def run_thread_crawler1(config, redis_connection):
    url_position_lock = threading.Semaphore(value=1)
    url_insertion_lock = threading.Semaphore(value=1)

    kwargs = {
        'redis_connection': redis_connection,
        'max_urls': config['max_urls'],
        'url_position_lock': url_position_lock,
        'url_insertion_lock': url_insertion_lock,
    }

    worker1 = MyThreadCrawler1(kwargs=kwargs)
    worker2 = MyThreadCrawler1(kwargs=kwargs)

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


def run_process_crawler1(config, redis_connection):
    url_position_lock = multiprocessing.Semaphore(value=1)
    url_insertion_lock = multiprocessing.Semaphore(value=1)

    kwargs = {
        'redis_connection': redis_connection,
        'max_urls': config['max_urls'],
        'url_position_lock': url_position_lock,
        'url_insertion_lock': url_insertion_lock,
    }

    worker1 = MyProcessCrawler1(kwargs=kwargs)
    worker2 = MyProcessCrawler1(kwargs=kwargs)

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


def run_thread_crawler2(config, redis_connection):
    kwargs = {
        'redis_connection': redis_connection,
        'max_urls': config['max_urls'],
    }

    worker1 = MyThreadCrawler2(kwargs=kwargs)
    worker2 = MyThreadCrawler2(kwargs=kwargs)
    worker3 = MyThreadCrawler2(kwargs=kwargs)
    worker4 = MyThreadCrawler2(kwargs=kwargs)

    print("starting to scrape...")
    t0 = time.time()

    worker1.start()
    worker2.start()
    worker3.start()
    worker4.start()

    worker1.join()
    worker2.join()
    worker3.join()
    worker4.join()

    t1 = time.time()
    print("finished scraping...")
    elapsed_time = round(t1 - t0, 2)
    print("elapsed scraping time: {} seconds".format(elapsed_time))
    print('-------------------------')


def run_process_crawler2(config, redis_connection):
    kwargs = {
        'redis_connection': redis_connection,
        'max_urls': config['max_urls'],
    }

    worker1 = MyProcessCrawler2(kwargs=kwargs)
    worker2 = MyProcessCrawler2(kwargs=kwargs)
    worker3 = MyProcessCrawler2(kwargs=kwargs)
    worker4 = MyProcessCrawler2(kwargs=kwargs)

    print("starting to scrape...")
    t0 = time.time()

    worker1.start()
    worker2.start()
    worker3.start()
    worker4.start()

    worker1.join()
    worker2.join()
    worker3.join()
    worker4.join()

    t1 = time.time()
    print("finished scraping...")
    elapsed_time = round(t1 - t0, 2)
    print("elapsed scraping time: {} seconds".format(elapsed_time))
    print('-------------------------')


def main():
    print('-------------------------')
    print("configuring...")

    config = load_config()
    redis_connection = get_redis_connection(config)
    initialize_redis_db(redis_connection, config['root_url'])

    run_thread_crawler1(config, redis_connection)
    #  run_process_crawler1(config, redis_connection)

    #  run_thread_crawler2(config, redis_connection)
    #  run_process_crawler2(config, redis_connection)


if __name__ == '__main__':
    main()
