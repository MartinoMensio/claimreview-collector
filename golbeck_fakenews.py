#!/bin/env python

import utils

directory = utils.data_location / 'golbeck_fakenews'

# this input file has been exported to TSV from `Fake News Stories.xlsx`
input_file = directory / 'intermediate' / 'data.tsv'

data = utils.read_tsv(input_file)

result = [{'url': row['URL of article'], 'label': 'fake', 'source': 'golbeck_fakenews'} for row  in data if row['Fake or Satire?'].strip() == 'Fake']

utils.write_json_with_path(result, directory, 'urls.json')

by_domain = utils.compute_by_domain(result)

utils.write_json_with_path(by_domain, directory, 'domains.json')

rebuttals = {el['URL of article']: {u.strip(): ['golbeck_fakenews'] for u in el['URL of rebutting article'].split('; ')} for el in data}

utils.write_json_with_path(rebuttals, directory, 'rebuttals.json')
