#!/bin/env python

import extruct
import json
import itertools



import utils

subfolder_path = utils.data_location / 'datacommons_factcheck'
source_file_path =  subfolder_path / 'source' / 'fact_checks_20180930.txt'
intermediate_path = subfolder_path / 'intermediate'
intermediate_file = intermediate_path / 'claimReviews.json'

def stage_1():
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


    extracted_claims = claims
    extracted_claims_and_rev = [{
        'claim': el['claimReviewed'],
        'review': el['reviewRating']['alternateName'],
        'url': el['url']
    } for el in claims]

    utils.write_json_with_path(extracted_claims, intermediate_path, 'claimReviews.json')

    print(labels_by_sources['Snopes.com'])

def stage_2():
    claims = utils.read_json(intermediate_file)
    # if you share a fact checking site, the fact checking site is true
    results = [{'url': c['url'], 'label': 'true', 'source': 'datacommons_factcheck'} for c in claims]
    utils.write_json_with_path(results, subfolder_path, 'urls.json')

    by_domain = utils.compute_by_domain(results)
    utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')


if __name__ == '__main__':
    stage_1()
    stage_2()