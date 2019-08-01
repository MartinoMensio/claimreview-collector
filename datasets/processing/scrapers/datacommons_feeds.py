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
    return data

def extract_claimreviews(data_feed):
    claim_reviews = []

    for item in data_feed['dataFeedElement']:
        if not item['item']:
            break
        for cr in item['item']:
            if cr:
                # some have "item": null
                claim_reviews.append(cr)

    utils.write_json_with_path(claim_reviews, subfolder_path, 'claimReviews.json')

    return claim_reviews

def extract_data(claim_reviews):
    fact_checking_urls = []
    for cr in claim_reviews:
        fact_checking_urls.append(claimreview.to_fact_checking_url(cr, 'datacommons_feeds'))
    utils.write_json_with_path(fact_checking_urls, subfolder_path, 'fact_checking_urls.json')


def get_credibility_measures(claim_review):
    rating = claimreview.get_claim_rating(claim_review)
    if rating is None:
        credibility = 0.0
        confidence = 0.0
    else:
        print(rating, claim_review['reviewRating'])
        credibility = (rating - 0.5) * 2
        confidence = 1.0
    return {'credibility': credibility, 'confidence': confidence}

def extract_graph_data_from_claim_review(claim_review):
    graph_data = []

    item_reviewed = claim_review.get('itemReviewed', {})
    appearances = item_reviewed.get('appearances', [])
    first_appearance = item_reviewed.get('firstAppearance', None)
    if first_appearance:
        appearances.append(first_appearance)

    appearances_urls = [el['url'] for el in appearances if el.get('url', None)]
    review_url = claim_review.get('url', None)
    review_rating = claim_review.get('reviewRating', {})

    if review_url:
        review_domain = utils.get_url_domain(review_url)
        graph_data.append((review_domain, {'@type': 'publishes', 'source': dataset}, review_url))
        for claim_url in appearances_urls:
            claim_domain = utils.get_url_domain(claim_url)
            graph_data.append((claim_domain, {'@type': 'publishes', 'source': dataset}, claim_url))
            graph_data.append((review_url, {
                    '@type': 'assesses',
                    'original': review_rating,
                    'credibility': get_credibility_measures(claim_review),
                    'source': dataset
                }, claim_url))


    return graph_data


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

def download_latest_feed():
    return download_feed(latest_feed)

def main():
    #download_all_feeds()
    feed_data = download_latest_feed()
    claim_reviews = extract_claimreviews(feed_data)
    extract_data(claim_reviews)
    #graph_data = extract_graph_data_from_feed(feed_data)
    #utils.write_json_with_path(graph_data, subfolder_path, 'graph_data.json')

if __name__ == "__main__":
    main()