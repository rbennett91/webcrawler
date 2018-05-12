import json
import multiprocessing
import threading
import time

import redis

from crawlers import (
    MyThreadCrawler1,
    MyThreadCrawler2,
    MyProcessCrawler1,
    MyProcessCrawler2,
)


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
    redis_connection.zadd('c1_sorted_url_set', 0, root_url)
    redis_connection.set('c1_next_url_position', 0)

    # create set and list for Crawler2 objects
    redis_connection.sadd('c2_url_set', root_url)
    redis_connection.lpush('c2_url_queue_list', root_url)


def run_thread_crawler1(config, redis_connection):
    url_position_lock = threading.Semaphore(value=1)
    url_insertion_lock = threading.Semaphore(value=1)

    kwargs = {
        'redis_connection': redis_connection,
        'min_urls': config['min_urls'],
        'url_position_lock': url_position_lock,
        'url_insertion_lock': url_insertion_lock,
    }

    worker1 = MyThreadCrawler1(kwargs=kwargs)
    worker2 = MyThreadCrawler1(kwargs=kwargs)
    worker3 = MyThreadCrawler1(kwargs=kwargs)
    worker4 = MyThreadCrawler1(kwargs=kwargs)

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


def run_process_crawler1(config, redis_connection):
    url_position_lock = multiprocessing.Semaphore(value=1)
    url_insertion_lock = multiprocessing.Semaphore(value=1)

    kwargs = {
        'redis_connection': redis_connection,
        'min_urls': config['min_urls'],
        'url_position_lock': url_position_lock,
        'url_insertion_lock': url_insertion_lock,
    }

    worker1 = MyProcessCrawler1(kwargs=kwargs)
    worker2 = MyProcessCrawler1(kwargs=kwargs)
    worker3 = MyProcessCrawler1(kwargs=kwargs)
    worker4 = MyProcessCrawler1(kwargs=kwargs)

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


def run_thread_crawler2(config, redis_connection):
    kwargs = {
        'redis_connection': redis_connection,
        'min_urls': config['min_urls'],
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
        'min_urls': config['min_urls'],
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
