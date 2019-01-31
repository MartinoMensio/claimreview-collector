#!/usr/bin/env python

import utils
import claimreview

dataset = 'datacommons_feeds'
subfolder_path = utils.data_location / 'datacommons_feeds'
input_file = subfolder_path / 'source' / 'data.json'

data = utils.read_json(input_file)
claimReviews = data['dataFeedElement']

results = [{'url': el['url'], 'label': 'true', 'source': 'datacommons_feeds'} for el in claimReviews]

fact_checking_urls = []
for cr in claimReviews:
    fact_checking_urls.append(claimreview.to_fact_checking_url(cr, 'datacommons_factcheck'))

utils.write_json_with_path(fact_checking_urls, subfolder_path, 'fact_checking_urls.json')

utils.write_json_with_path(results, subfolder_path, 'urls.json')

by_domain = utils.compute_by_domain(results)

utils.write_json_with_path(by_domain, subfolder_path, 'domains.json')
