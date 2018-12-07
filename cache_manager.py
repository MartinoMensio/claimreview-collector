"""
this module caches all the web GET requests using the folder "cache".
'index.json' contains a map between the md5 and the URL.
The reverse mapping/navigation can be simply obtained by computing the md5 of an URL
"""

import requests
import os
import json
import hashlib

from pathlib import Path

import unshortener


my_path = os.path.dirname(os.path.abspath(__file__))
cache_path = Path(my_path) / 'cache'
web_pages_path = cache_path / 'pages'
index_file = cache_path / 'index.json'

index = {}

def read_file(path):
    with open(path) as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def save_index():
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)

def string_to_md5(string):
    return hashlib.md5(string.encode()).hexdigest()

def url_to_filename(url):
    return '{}.cache'.format(string_to_md5(url))

def get(url, unshorten=False, force_refresh=False, headers={}):
    if unshorten:
        raise NotImplementedError()
    filename = url_to_filename(url)
    if filename in index and not force_refresh:
        # cached
        return read_file(web_pages_path / filename)
    else:
        # new
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print('WARN', response.status_code, 'for', url)
        body = response.text
        write_file(web_pages_path / filename, body)
        index[filename] = url
        save_index()
        return body




if not os.path.isdir(cache_path):
    os.makedirs(cache_path)
if not os.path.isdir(web_pages_path):
    os.makedirs(web_pages_path)
if os.path.isfile(index_file):
    index = json.loads(read_file(index_file))

