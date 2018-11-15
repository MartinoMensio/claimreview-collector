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
    },
    'fakenewsnet': {
        'urls': True,
        'domains': False
    },
    'rbutr': {
        'urls': False, # which class to assign them?
        'domains': False
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

urls_cnt = len(all_urls)
domains_cnt = len(all_domains)
fake_urls_cnt = len([el for el in all_urls if el['label'] == 'fake'])
fake_domains_cnt = len([el for el in all_domains if el['label'] == 'fake'])
print('#urls', urls_cnt, ': fake', fake_urls_cnt, 'true', urls_cnt - fake_urls_cnt)
print('#domains', domains_cnt, ': fake', fake_domains_cnt, 'true', domains_cnt - fake_domains_cnt)

utils.write_json_with_path(all_urls, utils.data_location, 'all_urls.json')
utils.write_json_with_path(all_domains, utils.data_location, 'all_domains.json')

# copy to backend
utils.write_json_with_path(all_urls, Path('../backend'), 'all_urls.json')
utils.write_json_with_path(all_domains, Path('../backend'), 'all_domains.json')
