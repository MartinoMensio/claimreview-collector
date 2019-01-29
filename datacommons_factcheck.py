#!/usr/bin/env python

import extruct
import json
import itertools
import os
from tqdm import tqdm
from collections import defaultdict


import utils
import claimreview

subfolder_path = utils.data_location / 'datacommons_factcheck'
source_file_path =  subfolder_path / 'source' / 'fact_checks_20180930.txt'
intermediate_path = subfolder_path / 'intermediate'
intermediate_file = intermediate_path / 'datacommons_claimReviews.json'

def load_jsonld():
    # read the file
    with open(source_file_path) as f:
        content = f.read()

    # extract the embedded metadata https://github.com/scrapinghub/extruct
    data = extruct.extract(content)

    claimReviews = data['json-ld']

    # some analysis of the labels to see how they are annotated
    labels = set([el['reviewRating']['alternateName'] for el in claimReviews])
    lambda_source = lambda el: el['author']['name']

    # group the labels by the author of the review, to see how each one of them uses the alternateName
    labels_by_sources = {k:set([el['reviewRating']['alternateName'] for el in v]) for k, v in itertools.groupby(sorted(claimReviews, key=lambda_source), key=lambda_source)}

    print('#claimReviews', len(claimReviews))
    print('#labels', len(labels))
    #print('labels', labels)
    print('#label for each source', {k:len(v) for k,v in labels_by_sources.items()})

    # save the original claimReviews
    utils.write_json_with_path(claimReviews, intermediate_path, 'datacommons_claimReviews.json')

    return claimReviews

def get_claimreviews_from_factcheckers(original_claimReviews):
    result = []

    # retrieve the full claimReview from the fact checking website
    for idx, c in enumerate(tqdm(claimReviews)):
        # get the correct URL (some of them are wrong in the original dataset)
        fixed_url = claimreview.get_corrected_url(c['url'])

        # this part with id and file saving is just to be able to restore the operation after a failure so that the single claims are saved onto disk on by one
        id = utils.string_to_md5(fixed_url)
        partial_file_name = '{}.json'.format(id)
        partial_file_path = subfolder_path / 'intermediate' / 'single_claims' / partial_file_name
        if os.path.isfile(partial_file_path):
            # if it's been already saved, read it
            partial = utils.read_json(partial_file_path)
        else:
            # otherwise download the original claimReview from the fact checker
            url, partial = claimreview.retrieve_claimreview(c['url'])
            # and save it to disk
            utils.write_json_with_path(partial, subfolder_path / 'intermediate' / 'single_claims', partial_file_name)
        if not partial:
            # in this case there is no claimReview metadata on the fact checker website
            #print(c['url'])
            pass
        if len(partial):
            # there can be multiple claimReviews in a single fact checking page
            for j, claimReview in enumerate(partial):
                # save this in the result
                #result['{}::{}'.format(fixed_url, j)] = claimReview
                result.append(claimReview)

    return result


if __name__ == '__main__':
    claimReviews = load_jsonld()

    # if you share a fact checking site, the fact checking site is true
    urls = [{'url': c['url'], 'label': 'true', 'source': 'datacommons_factcheck'} for c in claimReviews]

    # retrieve the claimReviews with more properties
    claimReviews_full = get_claimreviews_from_factcheckers(claimReviews)
    # save to file
    utils.write_json_with_path(claimReviews_full, subfolder_path, 'claimReviews.json')

    # rebuttals is a dict that associates each URL with other URLs that are related. In this case it is for suggesting to read the fact checking article
    rebuttals = defaultdict(lambda: defaultdict(list))
    for claimReview in claimReviews_full:
        # retrieve the URL of the source of the claim (not always there)
        claim_urls = claimreview.get_claim_urls(claimReview)
        if claim_urls:
            print('claim', claim_urls)
            if 'properties' in claimReview:
                fixed_url = claimreview.get_corrected_url(claimReview['properties']['url'])
            else:
                fixed_url = claimreview.get_corrected_url(claimReview['url'])

            # save the found mapping between the claim URL and the factchecking URL
            rebuttals[claim_urls][fixed_url] = ['datacommons_factcheck']
            score = claimreview.get_claim_rating(claimReview)
            print(score)
            label = None
            if score != None:
                # convert to fake/true
                if score <= 0.30:
                    label = 'fake'
                if score >= 0.8:
                    label = 'true'
            if label:
                # save the label for the URL of the claim
                urls.append({'url': claim_urls, 'label': label, 'source': 'datacommons_factcheck'})

    print(len(rebuttals))

    utils.write_json_with_path(rebuttals, subfolder_path, 'rebuttals.json')


    utils.write_json_with_path(urls, subfolder_path, 'urls.json')

    # aggregate by domain
    by_domain = utils.compute_by_domain(urls)
    utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')
