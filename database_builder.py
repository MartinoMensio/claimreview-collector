#!/bin/env python

"""
This script is responsible to store into a DBMS all the datasets preprocessed.
For now the solution is a MongoDB database
"""

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
    domains = utils.read_json(utils.data_location / 'aggregated_domains.json')
    for d, data in domains.items():
        domains_collection.insert_one({
            '_id': d,
            'domain': d,
            'score': data
        })

def load_urls():
    urls = utils.read_json(utils.data_location / 'aggregated_urls.json')
    for u, data in urls.items():
        urls_collection.insert_one({
            '_id': u,
            'url': u,
            'score': data
        })

def load_rebuttals():
    rebuttals = utils.read_json(utils.data_location / 'aggregated_rebuttals.json')
    for u, data in rebuttals.items():
        rebuttals_collection.insert_one({
            '_id': u,
            'url': u,
            'rebuttals': data
        })

def load_claimReviews():
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



if __name__ == "__main__":
    clean_db()
    load_sources()
    load_domains()
    load_urls()
    load_rebuttals()
    load_claimReviews()

