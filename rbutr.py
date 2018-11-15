#!/bin/env python

import utils

location = utils.data_location / 'rbutr'

data = utils.read_tsv(location / 'source' / 'link_data.tab.txt')

results = [{'url': el['sourcepage'], 'label': 'fake', 'source': 'rbutr'} for el in data]

utils.write_json_with_path(results, location, 'urls.json')

domains = utils.compute_by_domain(results)

utils.write_json_with_path(results, location, 'domains.json')
