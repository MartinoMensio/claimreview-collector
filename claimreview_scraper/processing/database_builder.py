"""
This module is responsible to interface with MongoDB
"""

import os
import tldextract
import datetime
from pymongo import MongoClient, errors

from . import utils

MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
client = None
db = None
claimReviews_collection = None
lastupdated_collection = None
cache_collection = None
url_redirects_collection = None


def connect():
    global client, db, claimReviews_collection, lastupdated_collection, cache_collection, url_redirects_collection
    client = MongoClient(host=MONGO_HOST)
    db = client["claimreview_scraper"]
    # collections
    claimReviews_collection = db["claim_reviews"]
    lastupdated_collection = db["last_updated"]
    cache_collection = db["cache"]
    url_redirects_collection = client["utilities"]["url_redirects"]


def _check_connected(fn):
    def wrapper(*args, **kwargs):
        if not client:
            connect()
        return fn(*args, **kwargs)

    return wrapper


@_check_connected
def clean_db():
    claimReviews_collection.drop()


@_check_connected
def replace_safe(collection, document, key_property="_id"):
    document["updated"] = datetime.datetime.now()
    # the upsert sometimes fails, mongo does not perform it atomically
    # https://jira.mongodb.org/browse/SERVER-14322
    # https://stackoverflow.com/questions/29305405/mongodb-impossible-e11000-duplicate-key-error-dup-key-when-upserting
    try:
        collection.replace_one({"_id": document[key_property]}, document, upsert=True)
    except errors.DuplicateKeyError:
        collection.replace_one({"_id": document[key_property]}, document, upsert=True)
    document["updated"] = document["updated"].isoformat()


@_check_connected
def add_claimreviews_raw(claimreviews, clean=True):
    if len(claimreviews) < 1:
        raise ValueError("nothing")
    if clean:
        clean_db()
    claimReviews_collection.insert_many(claimreviews)
    print("added", len(claimreviews), "ClaimReviews")


@_check_connected
def add_ClaimReviews(scraper_name, claimreviews, clean=True):
    if len(claimreviews) < 1:
        raise ValueError("nothing")
    if clean:
        delete_ClaimReviews_from(scraper_name)
    for cr in claimreviews:
        cr["retrieved_by"] = scraper_name
    claimReviews_collection.insert_many(claimreviews)
    update_timestamp_of(scraper_name)
    print("added", len(claimreviews), "ClaimReviews from", scraper_name)


@_check_connected
def delete_ClaimReviews_from(scraper_name):
    claimReviews_collection.delete_many({"retrieved_by": scraper_name})


@_check_connected
def get_ClaimRewiews_from(scraper_name):
    return claimReviews_collection.find({"retrieved_by": scraper_name})


@_check_connected
def update_timestamp_of(scraper_name):
    lastupdated_collection.replace_one(
        {"_id": scraper_name},
        {"_id": scraper_name, "last_updated": datetime.datetime.now()},
        True,
    )


@_check_connected
def save_original_data(scraper_name, original_array, clean=True):
    if len(original_array) < 1:
        raise ValueError("nothing")
    collection = db[scraper_name]
    if clean:
        collection.drop()
    collection.insert_many(original_array)


@_check_connected
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


@_check_connected
def cache_get(url):
    return cache_collection.find_one({"_id": url})


@_check_connected
def cache_put(url, html):
    return cache_collection.replace_one({"_id": url}, {"_id": url, "html": html}, True)


@_check_connected
def create_indexes():
    # Not my business, I only deal with datasets
    # db['twitter_tweets'].create_index('user.id', name='user.id')

    # db['fact_checking_urls'].create_index('url', name='url')
    # db['fact_checking_urls'].create_index('claim_url', name='claim_url')
    pass


@_check_connected
def get_all_factchecking_urls():
    return list(claimReviews_collection.aggregate([{"$group": {"_id": "$url"}}]))
    # return claimReviews_collection.distinct('url')


@_check_connected
def get_count_unique_from_scraper(scraper_name):
    results = claimReviews_collection.aggregate(
        [{"$match": {"retrieved_by": scraper_name}}, {"$group": {"_id": "$url"}}]
    )
    return len(list(results))
    # return len(claimReviews_collection.distinct('url', {'retrieved_by': scraper_name}))


@_check_connected
def get_url_redirect(url):
    return url_redirects_collection.find_one({"_id": url})


@_check_connected
def save_url_redirect(from_url, to_url):
    if from_url != to_url:
        # just be sure not to go beyond the MongoDB limit of 1024
        url_mapping = {"_id": from_url[:1000], "to": to_url}
        return replace_safe(url_redirects_collection, url_mapping)
