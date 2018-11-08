#!/bin/env python

# puts together all the datasets

import glob

import utils

results = []
for part in glob.glob(str(utils.data_location / '*/result.json')):
    content = utils.read_json(part)
    results.extend(content)

utils.write_json_with_path(results, utils.data_location, 'all.json')