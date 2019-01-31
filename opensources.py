#!/usr/bin/env python

import utils
import claimreview

subfolder_opensources = utils.data_location / 'opensources'
subfolder_melissa = utils.data_location / 'melissa_zimdars'

def process(data, output_folder, source):
    properties = ['type', '2nd type', '3rd type']
    results = []
    # find the properties belonging to the mappings in the samples, and assign a single label
    for domain, props in data.items():
        looking_at = [prop_value for prop_name, prop_value in props.items() if prop_name in properties and prop_value]
        #print(looking_at)
        classes = set([a for a in [claimreview.simplify_label(el) for el in looking_at] if a])
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
