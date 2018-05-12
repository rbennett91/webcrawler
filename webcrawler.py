import argparse
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


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--crawler-type",
        help="Choose a crawler type: <crawler1|crawler2>",
        default="crawler1"
    )
    parser.add_argument(
        "-w",
        "--worker-type",
        help="Choose a worker type: <thread|process>",
        default="thread"
    )
    parser.add_argument(
        "-n",
        "--num_workers",
        help="How many workers? <1|2|3|...>",
        type=int,
        default=1
    )
    args = parser.parse_args()

    if args.crawler_type not in ('crawler1', 'crawler2'):
        raise argparse.ArgumentTypeError("Unknown crawler type. Exiting.")

    if args.worker_type not in ('thread', 'process'):
        raise argparse.ArgumentTypeError("Unknown worker type. Exiting.")

    return args


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
    # clear redis database
    redis_connection.flushdb()

    # create sorted set and counter for Crawler1 objects
    redis_connection.zadd('c1_sorted_url_set', 0, root_url)
    redis_connection.set('c1_next_url_position', 0)

    # create set and list for Crawler2 objects
    redis_connection.sadd('c2_url_set', root_url)
    redis_connection.lpush('c2_url_queue_list', root_url)


def crawl(args, config, redis_connection):
    if args.crawler_type == 'crawler1':
        if args.worker_type == 'thread':
            Crawler = MyThreadCrawler1
            url_position_lock = threading.Semaphore(value=1)
            url_insertion_lock = threading.Semaphore(value=1)
        elif args.worker_type == 'process':
            Crawler = MyProcessCrawler1
            url_position_lock = multiprocessing.Semaphore(value=1)
            url_insertion_lock = multiprocessing.Semaphore(value=1)

        kwargs = {
            'url_position_lock': url_position_lock,
            'url_insertion_lock': url_insertion_lock,
        }

    elif args.crawler_type == 'crawler2':
        if args.worker_type == 'thread':
            Crawler = MyThreadCrawler2
        elif args.worker_type == 'process':
            Crawler = MyProcessCrawler2

        kwargs = {}

    kwargs.update(
        {
            'redis_connection': redis_connection,
            'min_urls': config['min_urls'],
        }
    )

    print("starting to scrape...")
    t0 = time.time()

    workers = []
    for w in range(args.num_workers):
        worker = Crawler(kwargs=kwargs)
        workers.append(worker)
        worker.start()

    for worker in workers:
        worker.join()

    t1 = time.time()
    print("finished scraping...")
    elapsed_time = round(t1 - t0, 2)
    print("elapsed scraping time: {} seconds".format(elapsed_time))
    print('-------------------------')


def main():
    args = parse_arguments()

    print('-------------------------')
    print("configuring...")

    config = load_config()
    redis_connection = get_redis_connection(config)
    initialize_redis_db(redis_connection, config['root_url'])

    crawl(args, config, redis_connection)


if __name__ == '__main__':
    main()
