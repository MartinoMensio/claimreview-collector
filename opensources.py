#!/bin/env python

import utils

subfolder_opensources = utils.data_location / 'opensources'
subfolder_melissa = utils.data_location / 'melissa_zimdars'

def process(data, output_folder, source):
    mappings = {
        'fake': 'fake',
        'bias': 'fake',
        'conspiracy': 'fake',
        'junksci': 'fake',
        'hate': 'fake',
        'clickbait': 'fake',
        #'unreliable': 'fake',
        'reliable': 'true'
    }
    properties = ['type', '2nd type', '3rd type']
    results = []
    # find the properties belonging to the mappings in the samples, and assign a single label
    for domain, props in data.items():
        looking_at = [prop_value for prop_name, prop_value in props.items() if prop_name in properties and prop_value]
        #print(looking_at)
        classes = set(mappings[el] for el in looking_at if el in mappings)
        if len(classes) != 1:
            print(domain, classes)
            continue
        label = classes.pop()
        results.append({'domain': domain, 'label': label, 'source': source})

    utils.write_json_with_path(results, output_folder, 'domains.json')

data_opensources = utils.read_json(subfolder_opensources / 'source' / 'sources' / 'sources.json')
data_melissa_tsv = utils.read_tsv(subfolder_melissa / 'source' / 'melissa_zimdars_spreadsheet.tsv')
data_melissa = {el['url']: el for el in data_melissa_tsv}

process(data_opensources, subfolder_opensources, 'opensources')
process(data_melissa, subfolder_melissa, 'melissa_zimdars')
