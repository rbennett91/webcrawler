### What is this?
This is a programming exercise exploring Redis and concurrency + parallelism
in Python.

##### Why?
I wanted to learn more about Redis-- it's an interesting tool with many uses.

##### How does it work?
This system creates two types of webcrawlers (described in detail further below)

### Installation

##### Requirements
This project was built with Python 3.6.5 and Redis 4.0.9 on Ubuntu 18.04.
Depending on your system, you might might need to install a redis server.
Local package managers should have a copy of it, but newer versions are
available at https://redis.io/download. You'll need both Python & Redis,
plus a couple packages from the Python Package Index.

##### Setup
Clone this repository & `cd` into it:
* ```git clone https://github.com/rbennett91/webcrawler.git```
* ```cd webcrawler```

Create and activate a python virtual environment:
* ```python3 -m venv venv/```
* ```source venv/bin/activate```

Install packages from pip:
* ```pip3 install -r requirements.txt```

Create a configuration file:
* ```cp config.json.example config.json```

Add settings to `config.json`:
* the redis `host` value expects an IP address of the redis host. Use `127.0.0.1`
if installed locally
* `root_url`: the crawler's starting url. Example: "https://cs.purdue.edu"

### Usage
You'll need to activate the virtual environment and configure the settings
file before running the crawler.

##### Running the crawler
The script creates two `MyThreadCrawler` objects and runs them to completion.
To run processes instead of threads, comment out the `MyThreadCrawler`s and
instantiate `MyProcessCrawler` objects. Command line arguments were too
ambitious for this project :)

Run the code with:
* ```python3 ./webcrawler.py```

##### Inspecting Redis
Open the Redis command line utility & connect to the database:
* ```redis-cli```
* ```select <database_number>```, where <database_number> is the `db` value inside `config.json`
* <more to come>

### Observations

### References
Here are some of the more useful & interesting references I used while exploring:

Redis Documentation:
* https://redis.io/topics/data-types-intro
* https://redis.io/topics/data-types#sorted-sets
* https://redis.io/topics/data-types#sets
* https://redis.io/topics/data-types#lists
* https://redis.io/commands#sorted_set
* https://redis.io/commands#set
* https://redis.io/commands#list

Miscellaneous books & talks:
* Raymond Hettinger talk on concurrency: https://www.youtube.com/watch?v=9zinZmE3Ogk
* _Learning Concurrency in Python_ by Elliot Forbes: https://www.packtpub.com/application-development/learning-concurrency-python
