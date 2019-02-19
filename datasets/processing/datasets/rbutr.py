#!/usr/bin/env python

import os
from collections import defaultdict
from tqdm import tqdm

from .. import utils
from .. import unshortener

location = utils.data_location / 'rbutr'

def main():
    data = utils.read_tsv(location / 'source' / 'link_data.tab.txt')

    results = [{'url': el['sourcepage'], 'label': 'fake', 'source': 'rbutr'} for el in data]

    utils.write_json_with_path(results, location, 'urls.json')

    domains = utils.compute_by_domain(results)

    utils.write_json_with_path(results, location, 'domains.json')


    rebuttals = defaultdict(lambda: defaultdict(list))
    for row in data:
        rebuttals[row['sourcepage']][row['rebuttalpage']].append('rbutr')

    utils.write_json_with_path(rebuttals, location, 'rebuttals.json')

    # check which urls still exist

    rbutr_mapping_location = location / 'intermediate'
    rbutr_mapping_path = rbutr_mapping_location / 'mappings.json'
    mappings = {}
    if os.path.isfile(rbutr_mapping_path):
        mappings = utils.read_json(rbutr_mapping_path)
    rbutr_urls = set()
    for row in data:
        rbutr_urls.add(row['sourcepage'])
        rbutr_urls.add(row['rebuttalpage'])
    for idx, u in enumerate(tqdm(rbutr_urls)):
        #print(u)
        unshortener.unshorten(u)
        if idx % 10 == 0:
            utils.write_json_with_path(mappings, rbutr_mapping_location, 'mappings.json')

    utils.write_json_with_path(mappings, rbutr_mapping_location, 'mappings.json')
