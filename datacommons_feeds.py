#!/usr/bin/env python

import utils

dataset = 'datacommons_feeds'
subfolder_path = utils.data_location / 'datacommons_feeds'
input_file = subfolder_path / 'source' / 'data.json'

data = utils.read_json(input_file)

results = [{'url': el['url'], 'label': 'true', 'source': 'datacommons_feeds'} for el in data['dataFeedElement']]

utils.write_json_with_path(results, subfolder_path, 'urls.json')

by_domain = utils.compute_by_domain(results)

utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')
