#!/usr/bin/env python

import csv
import requests
import os

import utils
import claimreview

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
fact_checking_urls = []

#Download the links to politifacts
for f_name in ids_set:
    intermediate_folder = subfolder_path / 'intermediate'
    file_path = intermediate_folder / f_name
    url = url_template.format(f_name.split('.')[0])
    if not os.path.isfile(file_path):
        continue # the api has been disabled
        """
        print('downloading', url)
        response = requests.get(url=url)
        if response.status_code != 200:
            print('error downloading', url)
            continue
        utils.write_file_with_path(response.text, intermediate_folder, f_name)
        """

    # politifact is taken as true
    politifact_details = utils.read_json(file_path)
    canonical_url = 'https://www.politifact.com{}'.format(politifact_details['canonical_url'])
    urls.append({'url': canonical_url, 'label': 'true', 'source': 'liar'})

    matching = [el for el in data_all if el[0] == f_name][0]
    claim = matching[2]
    original_label = matching[1]
    label = claimreview.simplify_label(original_label)

    url = canonical_url

    fact_checking_urls.append({
        'url': url,
        'source': 'liar',
        'claim': claim,
        'label': label,
        'original_label': original_label
    })

utils.write_json_with_path(fact_checking_urls, subfolder_path, 'fact_checking_urls.json')

utils.write_json_with_path(urls, subfolder_path, 'urls.json')

by_domain = utils.compute_by_domain(urls)

utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')
