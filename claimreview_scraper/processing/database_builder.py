"""
This module is responsible to interface with MongoDB
"""

import os
import tldextract
import datetime
from pymongo import MongoClient, errors

from . import utils

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')

client = MongoClient(host=MONGO_HOST)

db = client['claimreview_scraper']

claimReviews_collection = db['claim_reviews']
lastupdated_collection = db['last_updated']
cache_collection = db['cache']
url_redirects_collection = client['utilities']['url_redirects']

def clean_db():
    claimReviews_collection.drop()

def replace_safe(collection, document, key_property='_id'):
    document['updated'] = datetime.datetime.now()
    # the upsert sometimes fails, mongo does not perform it atomically
    # https://jira.mongodb.org/browse/SERVER-14322
    # https://stackoverflow.com/questions/29305405/mongodb-impossible-e11000-duplicate-key-error-dup-key-when-upserting
    try:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)
    except errors.DuplicateKeyError:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)
    document['updated'] = document['updated'].isoformat()

def add_claimreviews_raw(claimreviews, clean=True):
    if len(claimreviews) < 1:
        raise ValueError('nothing')
    if clean:
        clean_db()
    claimReviews_collection.insert_many(claimreviews)
    print('added', len(claimreviews), 'ClaimReviews')

def add_ClaimReviews(scraper_name, claimreviews, clean=True):
    if len(claimreviews) < 1:
        raise ValueError('nothing')
    if clean:
        delete_ClaimReviews_from(scraper_name)
    for cr in claimreviews:
        cr['retrieved_by'] = scraper_name
    claimReviews_collection.insert_many(claimreviews)
    update_timestamp_of(scraper_name)
    print('added', len(claimreviews), 'ClaimReviews from', scraper_name)

def delete_ClaimReviews_from(scraper_name):
    claimReviews_collection.delete_many({'retrieved_by': scraper_name})

def get_ClaimRewiews_from(scraper_name):
    return claimReviews_collection.find({'retrieved_by': scraper_name})

def update_timestamp_of(scraper_name):
    lastupdated_collection.replace_one({'_id': scraper_name}, {'_id': scraper_name, 'last_updated': datetime.datetime.now()}, True)

def save_original_data(scraper_name, original_array, clean=True):
    if len(original_array) < 1:
        raise ValueError('nothing')
    collection = db[scraper_name]
    if clean:
        collection.drop()
    collection.insert_many(original_array)

def get_original_data(scraper_name):
    return db[scraper_name].find()

# def load_claimReviews():
#     claimReviews_collection.drop()

#     claimReviews = utils.read_json(utils.data_location / 'aggregated_claimReviews.json')
#     claimReviews_collection.insert_many(claimReviews)
#     """
#     for claimReview in claimReviews:
#         claimReviews_collection.insert_one(claimReview)
#     """

def cache_get(url):
    return cache_collection.find_one({'_id': url})

def cache_put(url, html):
    return cache_collection.replace_one({'_id': url}, {'_id': url, 'html': html}, True)


def create_indexes():
    # Not my business, I only deal with datasets
    #db['twitter_tweets'].create_index('user.id', name='user.id')

    # db['fact_checking_urls'].create_index('url', name='url')
    # db['fact_checking_urls'].create_index('claim_url', name='claim_url')
    pass


def get_all_factchecking_urls():
    return list(claimReviews_collection.aggregate([{"$group":{"_id":"$url"}}]))
    # return claimReviews_collection.distinct('url')


def get_count_unique_from_scraper(scraper_name):
    results = claimReviews_collection.aggregate([{"$match": {"retrieved_by": scraper_name}}, {"$group": {"_id": "$url"}}])
    return len(list(results))
    # return len(claimReviews_collection.distinct('url', {'retrieved_by': scraper_name}))

def get_url_redirect(url):
    return url_redirects_collection.find_one({'_id': url})

def save_url_redirect(from_url, to_url):
    if from_url != to_url:
        # just be sure not to go beyond the MongoDB limit of 1024
        url_mapping = {'_id': from_url[:1000], 'to': to_url}
        return replace_safe(url_redirects_collection, url_mapping)