#!/bin/env python

import utils

directory = utils.data_location / 'golbeck_fakenews'

# this input file has been exported to TSV from `Fake News Stories.xlsx`
input_file = directory / 'intermediate' / 'data.tsv'

data = utils.read_tsv(input_file)

urls = [{'url': row['URL of article'], 'label': 'fake', 'source': 'golbeck_fakenews'} for row  in data if row['Fake or Satire?'].strip() == 'Fake']

utils.write_json_with_path(urls, directory, 'urls.json')

sources = utils.read_json('sources.json')
# it's the author responsibility
source_url = sources['datasets']['golbeck_fakenews']['url']
verifier_url = sources['datasets']['golbeck_fakenews']['author']
claimReviews = []
for el in data:
    claimReview = {
        "@context": "http://schema.org",
        "@type": "ClaimReview",
        "datePublished": "2015-06-15",
        "url": source_url,
        "author": {
            "@type": "Person",
            "url": verifier_url
        },
        "claimReviewed": "",
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": -1,
            "bestRating": -1,
            "worstRating": -1,
            "alternateName": el['Fake or Satire?'].strip()
        },
        "itemReviewed": {
            "@type": "CreativeWork",
            "sameAs": el['URL of article']
        }
    }
    claimReviews.append(claimReview)

utils.write_json_with_path(claimReviews, directory, 'claimReviews.json')

by_domain = utils.compute_by_domain(urls)
utils.write_json_with_path(by_domain, directory, 'domains.json')

rebuttals = {el['URL of article']: {u.strip(): ['golbeck_fakenews'] for u in el['URL of rebutting article'].split('; ')} for el in data}

utils.write_json_with_path(rebuttals, directory, 'rebuttals.json')
