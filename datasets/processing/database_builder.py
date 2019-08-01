#!/usr/bin/env python

"""
This script is responsible to store into a DBMS all the datasets preprocessed.
For now the solution is a MongoDB database
"""

import tldextract
from pymongo import MongoClient

from . import utils

client = MongoClient()

# db = client['test_coinform']
db = client['datasets_resources']

domains_collection = db['domains']
domain_assessments_collection = db['domain_assessments']
urls_collection = db['urls']
rebuttals_collection = db['rebuttals']
sources_collection = db['sources']
fact_checkers_collection = db['fact_checkers']
claimReviews_collection = db['claim_reviews']
url_redirects_collection = db['url_redirects']

fact_checking_urls_collection = db['fact_checking_urls']

graph_nodes_collection = db['graph_nodes']
graph_links_collection = db['graph_links']

def clean_db():
    # they are already dropped in _zero methods
    domains_collection.drop()
    urls_collection.drop()
    rebuttals_collection.drop()
    sources_collection.drop()
    fact_checkers_collection.drop()
    fact_checking_urls_collection.drop()
    claimReviews_collection.drop()

def load_datasets():
    sources_collection.drop()

    sources = utils.read_sources()
    for k, v in sources.items():
        v['_id'] = k
        sources_collection.insert_one(v)


def load_fact_checkers(file_name='aggregated_fact_checkers.json'):
    fact_checkers_collection.drop()

    fact_checkers = utils.read_json(utils.data_location / file_name)
    for fc in fact_checkers:
        k = fc.get('id', None)
        if not k:
            k = fc['domain']
        k = k.replace('.', '_')
        fc['_id'] = k
        fact_checkers_collection.insert_one(fc)

def load_domains_zero(file_name='aggregated_domains.json'):
    domains_collection.drop()

    domains = utils.read_json(utils.data_location / file_name)
    for d, data in domains.items():
        d = get_url_domain(d)
        doc = {
            '_id': d,
            'domain': d,
            'score': data
        }
        domains_collection.replace_one({'_id': doc['_id']}, doc, upsert=True)

def load_domain_assessments(file_name='aggregated_domain_assessments.json'):
    domain_assessments_collection.drop()

    domain_assessments = utils.read_json(utils.data_location / file_name)
    domain_assessments_collection.insert_many(domain_assessments)

def load_url(url):
    raise NotImplementedError()

def load_urls_zero(file_name='aggregated_urls.json'):
    urls_collection.drop()

    urls = utils.read_json(utils.data_location / file_name)
    for u, data in urls.items():
        u = u[:1000]
        urls_collection.insert_one({
            '_id': u,
            'url': u,
            'score': data
        })

def load_fact_checking_urls_zero(file_name='aggregated_fact_checking_urls.json'):
    fact_checking_urls_collection.drop()

    fact_checking_urls = utils.read_json(utils.data_location / file_name)
    for fcu in fact_checking_urls:
        url = fcu.get('url', None)
        if url: url[:1000]
        claim_url = fcu.get('claim_url', '')
        if claim_url: claim_url[:1000]
    return fact_checking_urls_collection.insert_many(fact_checking_urls)

def load_rebuttals_zero(file_name='aggregated_rebuttals.json'):
    rebuttals_collection.drop()

    rebuttals = utils.read_json(utils.data_location / file_name)
    for u, data in rebuttals.items():
        u = u[:1000]
        rebuttals_collection.insert_one({
            '_id': u,
            'url': u,
            'rebuttals': data
        })


def load_claimReviews():
    claimReviews_collection.drop()

    claimReviews = utils.read_json(utils.data_location / 'aggregated_claimReviews.json')
    claimReviews_collection.insert_many(claimReviews)
    """
    for claimReview in claimReviews:
        claimReviews_collection.insert_one(claimReview)
    """

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
    # Not my business, I only deal with datasets
    #db['twitter_tweets'].create_index('user.id', name='user.id')

    db['fact_checking_urls'].create_index('url', name='url')
    db['fact_checking_urls'].create_index('claim_url', name='claim_url')


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

def get_fact_checking_urls(url):
    return fact_checking_urls_collection.find({'url': url})

def load_fact_checking_url(fact_checking_url):
    # fact_checking_url['_id'] = fact_checking_url['url']
    key = fact_checking_url.get('_id', None)
    if key:
        # this is an update
        return fact_checking_urls_collection.replace_one({'_id': fact_checking_url['_id']}, fact_checking_url, upsert=True)
    else:
        # let mongo generate the _id
        return fact_checking_urls_collection.insert_one(fact_checking_url)


def save_graph(graph):
    nodes = []
    for el_key, el in graph['nodes'].items():
        el['_id'] = el_key
        nodes.append(el)
    links = graph['links']

    graph_nodes_collection.drop()
    graph_links_collection.drop()

    graph_nodes_collection.insert_many(nodes)
    graph_links_collection.insert_many(links)

def main():
    print('don\'t use me directly! Run aggregate.py instead!!!')
    #clean_db()
    #load_sources()
    #load_domains_zero()
    #load_urls_zero()
    #load_rebuttals_zero()
    #load_claimReviews()
