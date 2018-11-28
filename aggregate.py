#!/bin/env python

# puts together all the datasets

import os
import json
import glob
import shutil
import signal
import sys
from pathlib import Path

import utils
import unshortener

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
    },
    'hyperpartisan': {
        'urls': False, # hyperpartisan does not mean fake
        'domains': False
    },
    'wikipedia': {
        'urls': False,
        'domains': True
    },
    'domain_list': {
        'urls': False,
        'domains': True
    },
    'melissa_zimdars': {
        'urls': False,
        'domains': True
    },
    'jruvika_fakenews': {
        'urls': True,
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

aggregated_urls = utils.aggregate(all_urls)
aggregated_domains = utils.aggregate(all_domains, 'domain')

utils.write_json_with_path(aggregated_urls, utils.data_location, 'aggregated_urls.json')
utils.write_json_with_path(aggregated_domains, utils.data_location, 'aggregated_domains.json')

# copy to backend
utils.write_json_with_path(aggregated_urls, Path('../backend'), 'aggregated_urls.json')
utils.write_json_with_path(aggregated_domains, Path('../backend'), 'aggregated_domains.json')

utils.print_stats(aggregated_urls)
utils.print_stats(aggregated_domains)

print('updating mappings, it may take a while')
mappings_file = utils.data_location / 'mappings.json'

mappings = {}
if os.path.isfile(mappings_file):
    with open(mappings_file) as f:
        mappings = json.load(f)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    with open(mappings_file, 'w') as f:
        json.dump(mappings, f, indent=2)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


to_be_mapped = [url for url in aggregated_urls.keys() if url not in mappings]
try:
    unshortener.unshorten_multiprocess(to_be_mapped, mappings)
except Exception as e:
    print('gotcha')
# save those damn mappings
with open(mappings_file, 'w') as f:
    json.dump(mappings, f, indent=2)