#!/usr/bin/env python
import requests

from .. import utils
from .. import claimreview

dataset = 'datacommons_feeds'
subfolder_path = utils.data_location / 'datacommons_feeds'
feed_url = 'https://storage.googleapis.com/datacommons-feeds/claimreview/latest/data.json'

def main():
    response = requests.get(feed_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    claimReviews = data['dataFeedElement']

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
