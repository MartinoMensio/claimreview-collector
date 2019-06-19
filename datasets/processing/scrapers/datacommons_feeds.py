#!/usr/bin/env python
import requests
import re
from xml.etree import ElementTree

from .. import utils
from .. import claimreview

dataset = 'datacommons_feeds'
subfolder_path = utils.data_location / 'datacommons_feeds'
feed_directory = 'https://storage.googleapis.com/datacommons-feeds/'
latest_feed = 'claimreview/latest/data.json'

def download_feed(feed_url):
    pieces = feed_url.split('/')
    if len(pieces) != 3:
        return
    version = pieces[1]
    response = requests.get(feed_directory + feed_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    utils.write_json_with_path(data, subfolder_path / 'source', version + '.json')

def extract_data(data_feed):
    claimReviews = data_feed['dataFeedElement']

    results = [{'url': el['url'], 'label': 'true', 'source': 'datacommons_feeds'} for el in claimReviews]

    fact_checking_urls = []
    claim_reviews = []
    for item in claimReviews:
        cr = item['item'][0]
        claim_reviews.append(cr)
        fact_checking_urls.append(claimreview.to_fact_checking_url(cr, 'datacommons_feeds'))

    utils.write_json_with_path(fact_checking_urls, subfolder_path, 'fact_checking_urls.json')

    utils.write_json_with_path(claimReviews, subfolder_path, 'claimReviews.json')

    utils.write_json_with_path(results, subfolder_path, 'urls.json')

    by_domain = utils.compute_by_domain(results)

    utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')

def download_all_feeds():
    response = requests.get(feed_directory)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    response_content = response.text
    # remove the namespace, also if single quoted https://stackoverflow.com/questions/34009992/python-elementtree-default-namespace
    response_content = re.sub(r"""\s(xmlns="[^"]+"|xmlns='[^']+')""", '', response_content, count=1)
    #print(response_content)
    root = ElementTree.fromstring(response_content)
    #print(root)
    for el in root.findall('Contents'):
        #print(el)
        key = el.find('Key').text
        print(key)
        download_feed(key)


def main():
    download_all_feeds()