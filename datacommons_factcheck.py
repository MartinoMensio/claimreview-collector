#!/bin/env python

import extruct
import json
import itertools



import utils

subfolder_name = 'datacommons_factcheck'
source_file_path = utils.location / subfolder_name / 'source' / 'fact_checks_20180930.txt'

with open(source_file_path) as f:
    content = f.read()

data = extruct.extract(content)

claims = data['json-ld']

labels = set([el['reviewRating']['alternateName'] for el in claims])
lambda_source = lambda el: el['author']['name']
labels_by_sources = {k:set([el['reviewRating']['alternateName'] for el in v]) for k, v in itertools.groupby(sorted(claims, key=lambda_source), key=lambda_source)}

print('#claims', len(claims))
print('#labels', len(labels))
print('labels', labels)
print('sources', {k:len(v) for k,v in labels_by_sources.items()})


extracted_claims_and_rev = [{
    'claim': el['claimReviewed'],
    'review': el['reviewRating']['alternateName'],
    'url': el['url']
} for el in claims]

#with open('exported.json', 'w') as f:
#    json.dump(extracted_claims_and_rev, f, indent=2)

print(labels_by_sources['Snopes.com'])