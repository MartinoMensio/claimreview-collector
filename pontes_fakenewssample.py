#!/usr/bin/env python

import utils

subfolder = utils.data_location / 'pontes_fakenewssample'

data = utils.read_tsv(subfolder / 'source' / 'resized_v2.csv', delimiter=',')

print(len(data))
print('loaded data')
types = set([el['type'] for el in data])
print(types)
label_maps = {
    'reliable': 'true',
    'clickbait': 'fake',
    'junksci': 'fake',
    'conspirancy': 'fake',
    'fake': 'fake'
}
urls = [{'url': el['url'], 'label': label_maps[el['type']], 'source': 'pontes_fakenewssample'} for el in data if el['type'] in label_maps]

utils.write_json_with_path(urls, subfolder, 'urls.json')
del data

by_domain = utils.compute_by_domain(urls)

utils.write_json_with_path(by_domain, subfolder, 'domains.json')