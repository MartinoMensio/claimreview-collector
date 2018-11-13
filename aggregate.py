#!/bin/env python

# puts together all the datasets

import glob
import shutil

import utils

results = []
for part in glob.glob(str(utils.data_location / '*/result.json')):
    content = utils.read_json(part)
    results.extend(content)

print(len(results), len(set([el['url'] for el in results])))

utils.write_json_with_path(results, utils.data_location, 'all.json')

# copy to backend
shutil.copy(utils.data_location / 'all.json', '../backend/urls.json')
