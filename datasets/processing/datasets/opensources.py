#!/usr/bin/env python

from .. import utils
from .. import claimreview

subfolder_opensources = utils.data_location / 'opensources'
subfolder_zimdars = utils.data_location / 'melissa_zimdars'

def process(data, output_folder, source):
    properties = ['type', '2nd type', '3rd type']
    results = []
    # find the properties belonging to the mappings in the samples, and assign a single label
    for domain, props in data.items():
        looking_at = [prop_value for prop_name, prop_value in props.items() if prop_name in properties and prop_value]
        #print(looking_at)
        classes = set([a for a in [claimreview.simplify_label(el) for el in looking_at] if a])
        if len(classes) != 1:
            #print(domain, classes)
            continue
        label = classes.pop()
        results.append({'domain': domain, 'label': label, 'source': source})

    utils.write_json_with_path(results, output_folder, 'domains.json')

def main(which='opensources'):
    if which == 'opensources':
        data_opensources = utils.read_json(subfolder_opensources / 'source' / 'sources' / 'sources.json')
        process(data_opensources, subfolder_opensources, 'opensources')
    if which == 'melissa_zimdars':
        data_zimdars_tsv = utils.read_tsv(subfolder_zimdars / 'source' / 'melissa_zimdars_spreadsheet.tsv')
        data_zimdars = {el['url']: el for el in data_zimdars_tsv}

        process(data_zimdars, subfolder_zimdars, 'melissa_zimdars')
