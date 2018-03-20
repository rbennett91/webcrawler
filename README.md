### What is this?
This is a programming exercise exploring Redis and concurrency in Python. 

##### Why?

### Installation

##### Requirements (python version, redis, venv)
This project was built with Python 3.5.2 and Redis version 4.0.8. Depending on
your system, you might might need to install a redis server. Local package 
managers should have a copy of it, but newer versions are available at
https://redis.io/download.

##### Setup
Clone this repository & `cd` into it:

```git clone https://github.com/rbennett91/webcrawler.git ; cd webcrawler```

Create and activate a python virtual environment:
```python3 -m venv venv/```

```source venv/bin/activate```

Install packages from pip:
```pip3 install -r requirements.txt```

Create a configuration file:
```cp config.json.example config.json```

Add settings to `config.json`
* the redis `host` key expects an IP address of the redis host. Use `127.0.0.1`
if installed locally
* `root_url`: a starting url where the crawler begins

### Usage

### Technologies used

### Observations

### References


### TODO:
###### add comments
