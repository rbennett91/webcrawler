### What is this?
This was a programming exercise exploring Redis and concurrency + parallelism in Python. Two different web crawlers were created, each (ab)using different Redis data structures, such as lists, sets, and sorted sets.

### Installation

##### Requirements
This project has been updated for Python 3.8.2 and Redis 5.0.7 on Ubuntu 20.04. It utilizes `requests` and `beautifulsoup4` to scrape URLs from websites.

##### Setup
Clone the codebase & set your working directory to the top level of the repository:
```
git clone https://github.com/rbennett91/webcrawler.git
cd webcrawler
```

Create and activate a Python virtual environment:
```
python3 -m venv venv/
source venv/bin/activate
```

Install pip packages:
```
pip install -r requirements.txt
```

Create a configuration file using the provided template:
```
cp config.json.example config.json
```

Add settings to `config.json` using your favorite text editor:
* the redis `host` value expects an IP address of the redis host. Use `127.0.0.1` if installed locally
* `root_url`: the crawler's starting url. Example: "https://cs.purdue.edu"

##### Running the crawler
The program accepts several command line arguments, namely choices of crawler type, worker type, number of workers, and an optional flag to clear Redis.
```
python webcrawler.py --help

usage: webcrawler.py [-h] [-c CRAWLER_TYPE] [-w WORKER_TYPE] [-n NUM_WORKERS] [-f]

optional arguments:
  -h, --help            show this help message and exit
  -c CRAWLER_TYPE, --crawler-type CRAWLER_TYPE
                        Choose a crawler type: <crawler1|crawler2>
  -w WORKER_TYPE, --worker-type WORKER_TYPE
                        Choose a worker type: <thread|process>
  -n NUM_WORKERS, --num_workers NUM_WORKERS
                        How many workers? <1|2|3|...>
  -f, --flush-database  Clears existing data in Redis
```

Example running crawler2 with 2 threads:
```
python webcrawler.py -c crawler2 -w thread -n 2 -f
```
The code needs comments (or a write-up here) to explain how each crawler works. TBD.

##### Inspecting Redis
Open the Redis command line utility & connect to the database. <database_number> is the `db` value inside `config.json`:
```
redis-cli
select <database_number>
```

Find total number of urls in `crawler1`'s sorted set:
```
zcard c1_sorted_url_set
```
Show `crawler1`'s urls:
```
# zrange c1_sorted_url_set <starting_position> <ending_position>
zrange c1_sorted_url_set 0 500
```

Find total number of urls in `crawler2`'s set:
```
scard c2_url_set
```
Show `crawler2`'s urls:
```
smembers c2_url_set
```

### References
Here are some of the more useful & interesting references I used while exploring:

Redis Documentation:
* https://redis.io/topics/data-types-intro
* https://redis.io/topics/data-types#lists
* https://redis.io/topics/data-types#sets
* https://redis.io/topics/data-types#sorted-sets
* https://redis.io/commands#sorted_set
* https://redis.io/commands#set
* https://redis.io/commands#list

Miscellaneous books & talks:
* Raymond Hettinger talk on concurrency: https://www.youtube.com/watch?v=9zinZmE3Ogk
* _Learning Concurrency in Python_ by Elliot Forbes: https://www.packtpub.com/application-development/learning-concurrency-python
