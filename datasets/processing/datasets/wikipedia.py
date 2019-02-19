#!/usr/bin/env python

from .. import utils

location = utils.data_location / 'wikipedia'

def main():
    data = utils.read_tsv(location / 'source' / 'wikipedia.tsv')

    domains = [{'domain': el['url'], 'label': el['label'], 'source': 'wikipedia'} for el in data]

    utils.write_json_with_path(domains, location, 'domains.json')
