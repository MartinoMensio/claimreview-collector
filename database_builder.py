#!/bin/env python

"""
This script is responsible to store into a DBMS all the datasets preprocessed.
For now the solution is a MongoDB database
"""

import tldextract
from pymongo import MongoClient

import utils

client = MongoClient()

db = client['test_coinform']

domains_collection = db['domains']
urls_collection = db['urls']
rebuttals_collection = db['rebuttals']
datasets_collection = db['datasets']
fact_checkers_collection = db['fact_checkers']
claimReviews_collection = db['claim_reviews']
url_redirects_collection = db['url_redirects']

def clean_db():
    domains_collection.drop()
    urls_collection.drop()
    rebuttals_collection.drop()
    datasets_collection.drop()
    fact_checkers_collection.drop()
    claimReviews_collection.drop()

def load_sources():
    datasets_collection.drop()
    fact_checkers_collection.drop()

    sources = utils.read_json('sources.json')
    datasets = sources['datasets']
    fact_checkers = sources['fact_checkers']
    for k, v in datasets.items():
        v['_id'] = k
        datasets_collection.insert_one(v)

    for k, v in fact_checkers.items():
        v['_id'] = k
        fact_checkers_collection.insert_one(v)

def load_domains():
    domains_collection.drop()

    domains = utils.read_json(utils.data_location / 'aggregated_domains.json')
    for d, data in domains.items():
        d = get_url_domain(d)
        doc = {
            '_id': d,
            'domain': d,
            'score': data
        }
        domains_collection.replace_one({'_id': doc['_id']}, doc, upsert=True)

def load_urls():
    urls_collection.drop()

    urls = utils.read_json(utils.data_location / 'aggregated_urls.json')
    for u, data in urls.items():
        urls_collection.insert_one({
            '_id': u,
            'url': u,
            'score': data
        })

def load_rebuttals():
    rebuttals_collection.drop()

    rebuttals = utils.read_json(utils.data_location / 'aggregated_rebuttals.json')
    for u, data in rebuttals.items():
        rebuttals_collection.insert_one({
            '_id': u,
            'url': u,
            'rebuttals': data
        })

def load_claimReviews():
    claimReviews_collection.drop()

    claimReviews = utils.read_json(utils.data_location / 'aggregated_claimReviews.json')
    for claimReview in claimReviews:
        claimReviews_collection.insert_one(claimReview)


def add_redirections(input_file_path):
    """The input file contains a JSON with k:v for redirections"""
    content = utils.read_json(input_file_path)
    for k,v in content.items():
        doc = {
            '_id': k[:1024], # the source
            'to': v
        }
        url_redirects_collection.update(doc, doc, upsert=True)

def create_indexes():
    db['twitter_tweets'].create_index('user.id', name='user.id')


def get_url_redirect(url):
    return url_redirects_collection.find_one({'_id': url})

def load_url_redirect(from_url, to_url):
    url_mapping = {'_id': from_url, 'to': to_url}
    return url_redirects_collection.replace_one({'_id': url_mapping['_id']}, url_mapping, upsert=True)

def get_url_domain(url):
    #parsed_uri = urlparse(url)
    #return str(parsed_uri.netloc)
    ext = tldextract.extract(url)
    result = '.'.join(part for part in ext if part)
    return result.lower()

if __name__ == "__main__":
    #clean_db()
    #load_sources()
    load_domains()
    #load_urls()
    #sload_rebuttals()
    #load_claimReviews()
