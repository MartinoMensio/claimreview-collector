#!/usr/bin/env python

import json
import csv
import utils

folder = utils.data_location / 'several27_fakenews'


# read the file without utils, 27.3 GB is too large for my pc
# TODO limit RAM used!!!
input_path = folder / 'source' / 'news_cleaned_2018_02_13.csv'
output_path = folder / 'intermediate'
output_file = output_path / 'unfiltered.json'

results = []
chunk_n = 0
with open(input_path) as f:
    reader = csv.DictReader(f, delimiter=',')
    for row in reader:
        results.append({'url': row['url'], 'label': row['type'], 'source': 'several27_fakenews'})
        if not len(results) % 1000000:
            print(len(results) * (chunk_n + 1) / 216212648)
            utils.write_json_with_path(results, output_path, 'unfiltered_{}.json'.format(chunk_n), indent=None)
            results = []
            chunk_n += 1
