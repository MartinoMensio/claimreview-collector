#!/bin/env python

import extruct
import json
import itertools
import os
from tqdm import tqdm


import utils
import claimreview

subfolder_path = utils.data_location / 'datacommons_factcheck'
source_file_path =  subfolder_path / 'source' / 'fact_checks_20180930.txt'
intermediate_path = subfolder_path / 'intermediate'
intermediate_file = intermediate_path / 'datacommons_claimReviews.json'

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

    utils.write_json_with_path(extracted_claims, intermediate_path, 'datacommons_claimReviews.json')

    print(labels_by_sources['Snopes.com'])
    return extracted_claims

def stage_2():
    claims = utils.read_json(intermediate_file)
    # if you share a fact checking site, the fact checking site is true
    results = [{'url': c['url'], 'label': 'true', 'source': 'datacommons_factcheck'} for c in claims]
    utils.write_json_with_path(results, subfolder_path, 'urls.json')

    by_domain = utils.compute_by_domain(results)
    utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')


if __name__ == '__main__':
    claims = stage_1()
    stage_2()

    claimReviews = {}
    for idx, c in enumerate(tqdm(claims)):
        #partial_file_name = 'cr_{}.json'.format(idx)
        fixed_url = claimreview.get_corrected_url(c['url'])
        id = utils.string_to_md5(fixed_url)
        partial_file_name = '{}.json'.format(id)
        partial_file_path = subfolder_path / 'intermediate' / 'single_claims' / partial_file_name
        if os.path.isfile(partial_file_path):
            partial = utils.read_json(partial_file_path)
        else:
            url, partial = claimreview.retrieve_claimreview(c['url'])
            utils.write_json_with_path(partial, subfolder_path / 'intermediate' / 'single_claims', partial_file_name)
        if not partial:
            #print(c['url'])
            pass
        if len(partial):
            if not len(partial) == 1:
                #print('more than one in', fixed_url)
                pass
            claimReview = partial[0]
            claim_urls = claimreview.get_claim_urls(claimReview)
            if claim_urls:
                print('claim', claim_urls)
            claimReviews[id] = claimReview

    utils.write_json_with_path(claimReviews, subfolder_path, 'claimReviews.json')
