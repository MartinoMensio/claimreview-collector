#!/usr/bin/env python

# puts together all the datasets

import os
import json
import glob
import shutil
import signal
import sys
from collections import defaultdict
from pathlib import Path

import utils
import unshortener

import database_builder


def merge_fact_checking_urls(old, new):
    if not old:
        result = {**new}
        result['source'] = [new['source']]
    else:
        # TODO fields that cannot be merged
        #if new['source'] not in old['source']:
        if 'label' in new and 'label' in old and new['label'] != old['label']:
            if new['label'] != None and old['label'] != None:
                print(old)
                print(new)
                raise ValueError()
        result = {**old, **{k:v for k,v in new.items() if v!=None}}
        print(old['source'], new['source'])
        result['source'] = list(set(old['source'] + [new['source']]))
    return result

# decide here what to aggregate
choice = {k if 'domain_list_' not in k else 'domain_list': {
    'urls': el['contains'].get('url_classification', False), # TODO rename to url_labels
    'domains': el['contains'].get('domain_classification', False), # TODO rename to domain_labels
    'rebuttals': el['contains'].get('rebuttal_suggestion', False), # TODO rename to rebuttals
    'claimReviews': el['contains'].get('claimReviews', False), # TODO rename to claim_reviews
    'fact_checking_urls': el['contains'].get('fact_checking_urls', False)
} for k, el in utils.read_json('sources.json')['datasets'].items()}

all_urls = []
all_domains = []
all_rebuttals = defaultdict(list)
all_claimreviews = []
all_fact_checking_urls = {}
for subfolder, config in choice.items():
    if config['urls']:
        urls = utils.read_json(utils.data_location / subfolder / 'urls.json')
        all_urls.extend(urls)
    if config['domains']:
        domains = utils.read_json(utils.data_location / subfolder / 'domains.json')
        all_domains.extend(domains)
    if config['rebuttals']:
        rebuttals = utils.read_json(utils.data_location / subfolder / 'rebuttals.json')
        for source_url, rebuttal_l in rebuttals.items():
            for rebuttal_url, source in rebuttal_l.items():
                all_rebuttals[source_url].append({
                    'url': rebuttal_url,
                    'source': source
                })
    if config['claimReviews']:
        claimReview = utils.read_json(utils.data_location / subfolder / 'claimReviews.json')
        all_claimreviews.extend(claimReview)
    if config['fact_checking_urls']:
        fact_checking_urls = utils.read_json(utils.data_location / subfolder / 'fact_checking_urls.json')
        for fcu in fact_checking_urls:
            match = database_builder.get_fact_checking_url(fcu['url'])
            merged = merge_fact_checking_urls(match, fcu)
            database_builder.load_fact_checking_url(merged)

# TODO

urls_cnt = len(all_urls)
domains_cnt = len(all_domains)
fake_urls_cnt = len([el for el in all_urls if el['label'] == 'fake'])
fake_domains_cnt = len([el for el in all_domains if el['label'] == 'fake'])
print('#urls', urls_cnt, ': fake', fake_urls_cnt, 'true', urls_cnt - fake_urls_cnt)
print('#domains', domains_cnt, ': fake', fake_domains_cnt, 'true', domains_cnt - fake_domains_cnt)

aggregated_urls = utils.aggregate(all_urls)
aggregated_domains = utils.aggregate(all_domains, 'domain')

utils.write_json_with_path(aggregated_urls, utils.data_location, 'aggregated_urls.json')
utils.write_json_with_path(aggregated_domains, utils.data_location, 'aggregated_domains.json')
utils.write_json_with_path(all_rebuttals, utils.data_location, 'aggregated_rebuttals.json')
utils.write_json_with_path(all_claimreviews, utils.data_location, 'aggregated_claimReviews.json')

# copy to backend
utils.write_json_with_path(aggregated_urls, Path('../backend'), 'aggregated_urls.json')
utils.write_json_with_path(aggregated_domains, Path('../backend'), 'aggregated_domains.json')
utils.write_json_with_path(all_rebuttals, Path('../backend'), 'aggregated_rebuttals.json')
utils.write_json_with_path(all_claimreviews, Path('../backend'), 'aggregated_claimReviews.json')

utils.print_stats(aggregated_urls)
utils.print_stats(aggregated_domains)

to_be_mapped = [url for url in aggregated_urls.keys()]
#unshortener.unshorten_multiprocess(to_be_mapped)
