#!/bin/env python

import utils

location = utils.data_location / 'wikipedia'

data = utils.read_tsv(location / 'source' / 'wikipedia.tsv')

domains = [{'domain': el['url'], 'label': el['label'], 'source': 'wikipedia'} for el in data]

utils.write_json_with_path(domains, location, 'domains.json')