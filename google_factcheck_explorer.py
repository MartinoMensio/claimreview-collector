#!/bin/env python

import json
import requests # not cache manager
import os

from dotenv import load_dotenv, find_dotenv
from collections import defaultdict

import utils
import claimreview

load_dotenv(find_dotenv())
subfolder_path = utils.data_location / 'google_factcheck_explorer'

def get_recent(lang='', offset=0, num_results=200000, query='list:recent'):
    params = {
        'hl': lang, # the language to search
        'num_results': num_results,
        'query': query,
        'force': 'false',
        'offset': offset
    }
    headers = {
        'dnt': '1',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-GB,en;q=0.9,it-IT;q=0.8,it;q=0.7,en-US;q=0.6',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'referer': 'https://toolbox.google.com/factcheck/explorer/search/list:recent;hl=en;gl=',
        'authority': 'toolbox.google.com',
        'cookie': os.environ.get('GOOGLE_FACTCHECK_EXPLORER_COOKIE')
    }
    response = requests.get('https://toolbox.google.com/factcheck/api/search', params=params, headers=headers)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    #print(response.text)
    #text = response.text[5:].encode().decode('utf-8', 'ignore')

    content = json.loads(response.text[5:])
    reviews = content[0][1]
    #with open('test.json', 'w') as f:
    #    json.dump(content, f, indent=2)

    results = []
    for r in reviews:
        try:
            claimReview = {
                '@context': "http://schema.org",
                "@type": "ClaimReview",
                #"datePublished": ?,
                'url': r[0][3][0][1],
                'claimReviewed': r[0][0],
                'author': {
                    "@type": "Organization",
                    "name": r[0][3][0][0][0],
                    "url": r[0][3][0][0][1],
                    #"image": ?,
                    #"sameAs": ?
                },
                'reviewRating': {
                    '@type': 'Rating',
                    'ratingValue': r[0][3][0][9][0] if (len(r[0][3][0]) > 9 and  len(r[0][3][0][9])) else -1,
                    'worstRating': r[0][3][0][9][1] if (len(r[0][3][0]) > 9 and  len(r[0][3][0][9])) else -1,
                    'bestRating': r[0][3][0][9][2] if  (len(r[0][3][0]) > 9 and len(r[0][3][0][9])) else -1,
                    'alternateName': r[0][3][0][3],
                    #"image": ?,
                },
                'itemReviewed': {
                    '@type': 'CreativeWork',
                    'author': {
                        '@type': 'Person',
                        'name': r[0][1][0],
                        'sameAs': r[0][4][0][1] if len(r[0][4]) else None
                    } if len(r[0][1]) else {}
                }
                #'claim_author': r[0][1][0] if len(r[0][1]) else None,
                #'id': r[0][2],
                #'review_author': r[0][3][0][0][0],
                #'review_title': r[0][3][0][8],
                #'claim_url': r[0][4][0][1] if len(r[0][4]) else None
            }
            results.append(claimReview)
        except IndexError as e:
            print(json.dumps(r))
            raise(e)
    print(len(results))
    return results, content

claimReviews, raw = get_recent()

utils.write_json_with_path(claimReviews, subfolder_path, 'claimReviews.json')
utils.write_json_with_path(raw, subfolder_path / 'intermediate', 'raw.json')

urls = []
rebuttals = defaultdict(lambda: defaultdict(list))
for j, claimReview in enumerate(claimReviews):
    claim_urls = claimreview.get_claim_urls(claimReview)
    fixed_url = claimReview['url']
    if claim_urls:
        rebuttals[claim_urls][fixed_url] = ['google_factcheck_explorer']
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
            urls.append({'url': claim_urls, 'label': label, 'source': 'google_factcheck_explorer'})

utils.write_json_with_path(claimReviews, subfolder_path, 'claimReviews.json')
utils.write_json_with_path(rebuttals, subfolder_path, 'rebuttals.json')


utils.write_json_with_path(urls, subfolder_path, 'urls.json')

by_domain = utils.compute_by_domain(urls)
utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')

fact_checkers = list(set([utils.get_url_domain(el['url']) for el in claimReviews]))
utils.write_json_with_path(fact_checkers, subfolder_path, 'fact_checkers.json')
