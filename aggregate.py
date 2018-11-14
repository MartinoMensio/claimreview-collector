#!/bin/env python

# puts together all the datasets

import glob
import shutil
from pathlib import Path

import utils

# decide here what to aggregate
choice = {
    'datacommons_factcheck': {
        'urls': True,
        'domains': False
    },
    'datacommons_feeds': {
        'urls': True,
        'domains': False
    },
    'mrisdal_fakenews': {
        'urls': False,
        'domains': True
    },
    'golbeck_fakenews': {
        'urls': True,
        'domains': False
    },
    'liar': {
        'urls': True,
        'domains': False
    },
    'buzzface': {
        'urls': True,
        'domains': False
    },
    'opensources': {
        'urls': False,
        'domains': True
    }
}

all_urls = []
all_domains = []
for subfolder, config in choice.items():
    if config['urls']:
        urls = utils.read_json(utils.data_location / subfolder / 'urls.json')
        all_urls.extend(urls)
    if config['domains']:
        domains = utils.read_json(utils.data_location / subfolder / 'domains.json')
        all_domains.extend(domains)


print(len(all_urls), len(all_domains))

utils.write_json_with_path(all_urls, utils.data_location, 'all_urls.json')
utils.write_json_with_path(all_domains, utils.data_location, 'all_domains.json')

# copy to backend
utils.write_json_with_path(all_urls, Path('../backend'), 'all_urls.json')
utils.write_json_with_path(all_domains, Path('../backend'), 'all_domains.json')
