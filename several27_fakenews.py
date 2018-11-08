#!/bin/env python

import csv
import utils

folder = utils.data_location / 'several27_fakenews'


# read the file without utils, 27.3 GB is too large for my pc
# TODO limit RAM used!!!
input_path = folder / 'source' / 'news_cleaned_2018_02_13.csv'
results = []
with open(input_path) as f:
    reader = csv.DictReader(f, delimiter=',')
    for row in reader:
        results.append({'url': row['url'], 'label': row['type'], 'source': 'several27_fakenews'})
        if not len(results) % 100000:
            print('.', end='', flush=True)

utils.write_json_with_path(results, folder / 'intermediate', 'unfiltered.json')
