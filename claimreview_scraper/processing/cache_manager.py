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

from . import unshortener
from . import utils
from . import database_builder


# cache_path = utils.data_location / '..' / 'cache'
# web_pages_path = cache_path / 'pages'
# index_file = cache_path / 'index.json'

index = {}

# def read_file(path):
#     with open(path) as f:
#         return f.read()

# def write_file(path, content):
#     with open(path, 'w') as f:
#         f.write(content)

def string_to_md5(string):
    return hashlib.md5(string.encode()).hexdigest()

def url_to_filename(url):
    return '{}.cache'.format(string_to_md5(url))

def get(url, unshorten=True, force_refresh=False, verify=True, headers={}):
    if unshorten:
        url_short = url
        url = unshortener.unshorten(url_short)
    cache_hit = database_builder.cache_get(url)
    if cache_hit and not force_refresh:
        # cached
        return cache_hit['html']
    else:
        # new
        response = requests.get(url, headers=headers, verify=verify)
        if response.status_code != 200:
            print('WARN', response.status_code, 'for', url)
        html = response.text
        database_builder.cache_put(url, html)
        return html




# if not os.path.isdir(cache_path):
#     os.makedirs(cache_path)
# if not os.path.isdir(web_pages_path):
#     os.makedirs(web_pages_path)
# if os.path.isfile(index_file):
#     index = json.loads(read_file(index_file))
