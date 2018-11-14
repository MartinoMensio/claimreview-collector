#!/bin/env python

import utils

subfolder = utils.data_location / 'opensources'

data = utils.read_json(subfolder / 'source' / 'sources' / 'sources.json')

mappings = {
    'fake': 'fake',
    'bias': 'fake',
    'hate': 'fake',
    'clickbait': 'fake',
    'unreliable': 'fake',
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
    results.append({'domain': domain, 'label': label, 'source': 'opensources'})

utils.write_json_with_path(results, subfolder, 'domains.json')
