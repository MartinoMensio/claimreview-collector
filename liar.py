#!/usr/bin/env python

import csv
import requests
import os

import utils

url_template = 'https://www.politifact.com/api/v/2/statement/{}/?format=json'

files_with_ids = ['test.tsv', 'train.tsv', 'valid.tsv']

subfolder_path = utils.data_location / 'liar'

data_all = []
for file_name in files_with_ids:
    data = utils.read_tsv(subfolder_path / 'source' / file_name, with_header=False)
    data_all.extend(data)

ids_set = set([el[0] for el in data_all])
print('1.json' in ids_set)

print('to download:', len(ids_set))

urls = []
#Download the links to politifacts
for f_name in ids_set:
    intermediate_folder = subfolder_path / 'intermediate'
    file_path = intermediate_folder / f_name
    url = url_template.format(f_name.split('.')[0])
    if not os.path.isfile(file_path):
        print('downloading', url)
        response = requests.get(url=url)
        if response.status_code != 200:
            print('error downloading', url)
            continue
        utils.write_file_with_path(response.text, intermediate_folder, f_name)

    # politifact is taken as true
    politifact_details = utils.read_json(file_path)
    canonical_url = 'https://politifact.com/{}'.format(politifact_details['canonical_url'])
    urls.append({'url': canonical_url, 'label': 'true', 'source': 'liar'})

utils.write_json_with_path(urls, subfolder_path, 'urls.json')

by_domain = utils.compute_by_domain(urls)

utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')
