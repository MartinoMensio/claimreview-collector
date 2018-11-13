#!/bin/env python

import utils

directory = utils.data_location / 'golbeck_fakenews'

# this input file has been exported to TSV from `Fake News Stories.xlsx`
input_file = directory / 'intermediate' / 'data.tsv'

data = utils.read_tsv(input_file)

url_with_labels = {list(el.items())[1][1]: list(el.items())[2][1].strip().lower() for el in data}

result = [{'url': k, 'label': v, 'source': 'golbeck_fakenews'} for k,v  in url_with_labels.items() if v == 'fake']

utils.write_json_with_path(result, directory, 'urls.json')

by_domain = utils.compute_by_domain(result)

utils.write_json_with_path(by_domain, directory, 'domains.json')
