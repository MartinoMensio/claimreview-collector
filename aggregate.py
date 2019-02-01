#!/usr/bin/env python

# puts together all the datasets

import os
import json
import glob
import shutil
import signal
import sys
from dateutil import parser
from unidecode import unidecode
from collections import defaultdict
from pathlib import Path

import utils
import unshortener

import database_builder

def normalise_str(string):
    string = unidecode(string)
    string = string.lower()
    string = string.replace('"', '')
    string = string.replace('\'', '')
    string = string.replace('  ', ' ')
    return string

def select_best_candidate(fcu, matches):
    """Determine whether the fact_checking_url should be matched with any of the candidates, otherwise return None"""
    # the ones that pass the compulsory comparison
    matching_criteria = []
    affinities = []
    for m in matches:
        # the URL has been already compared
        if m['url'] == fcu['url']:
            matching_criteria.append(m)
            affinities.append(0)
    for idx, m in enumerate(matching_criteria):
        for k, v in fcu.items():
            if k == 'source':
                # the source has not to be compared
                continue
            if v and k in m and m[k]:
                prev = m[k]
                cur = v
                if k == 'claim':
                    # text normalisation
                    prev = normalise_str(prev)
                    cur = normalise_str(cur)
                if k == 'date':
                    prev = parser.parse(prev).date()
                    cur = parser.parse(cur).date()
                if k == 'original_label':
                    # ignore this property, too sensitive. There is already the 'label'
                    continue

                if prev != cur:
                    # if some values are different, this is a different claimReview
                    print(k, m['url'], v, m[k])
                    affinities[idx] = -50
                else:
                    affinities[idx] += 1

    # if len(matching_criteria):
    #     print(len(matching_criteria))
    #     print(affinities)
    #print([json.dump({k: v for k,v in el.items() if k != '_id'}, sys.stdout, indent=2) for el in matching_criteria])
    #exit(0)

    best = None
    best_affinity = -1
    for idx, (affinity, m) in enumerate(zip(affinities, matching_criteria)):
        if affinity >= 0:
            if affinity > best_affinity:
                best = m
                best_affinity = affinity

    # if best:
    #     print('going to merge', best, fcu)

    return best


def merge_fact_checking_urls(old, new):
    if not old:
        result = {**new}
        result['source'] = [new['source']]
    else:
        # TODO fields that cannot be merged
        #if new['source'] not in old['source']:
        if 'label' in new and 'label' in old and new['label'] != old['label']:
            if new['label'] != None and old['label'] != None:
                if new['claim'] != old['claim']:
                    raise ValueError('retry')
                    # TODO this will be fixed shortly
                else:
                    print(old)
                    print(new)
                    raise ValueError('abort')
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
            # mongo limits on indexed values
            fcu['url'] = fcu['url'][:1000]
            if fcu.get('claim_url', None): fcu['claim_url'][:1000]


            matches = database_builder.get_fact_checking_urls(fcu['url'])
            candidate = select_best_candidate(fcu, matches)
            merged = merge_fact_checking_urls(candidate, fcu)
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
