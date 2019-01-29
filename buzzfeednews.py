#!/usr/bin/env python

import utils

location = utils.data_location / 'buzzfeednews'

source_location = location / 'source' / '2018-12-fake-news-top-50' / 'data'
all_domains = utils.read_tsv(source_location / 'sites_2016.csv', delimiter=',') +\
            utils.read_tsv(source_location / 'sites_2017.csv', delimiter=',') + \
            utils.read_tsv(source_location / 'sites_2018.csv', delimiter=',')

single_domains = set([el['domain'] for el in all_domains])

domains = [{'domain': el, 'label': 'fake', 'source': 'buzzfeednews'} for el in single_domains]

print(len(domains))

utils.write_json_with_path(domains, location, 'domains.json')
