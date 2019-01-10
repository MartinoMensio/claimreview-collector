#!/bin/env python

import utils

location = utils.data_location / 'domain_list'

def default_mapping():
    return {
        'domain_col': 'domain',
        'label_col': 'label',
        'true_vals': ['true'],
        'fake_vals': ['fake']
    }

def fakenewswatch_mapping():
    default = default_mapping()
    default['fake_vals'] = ['fake_hoax', 'clickbait']
    default['true_vals'] = []
    return default

def usnews_mapping():
    default = default_mapping()
    default['fake_vals'] = ['hoax']
    return default

def politifact_mapping():
    default = default_mapping()
    default['label_col'] = 'Type of site'
    default['fake_vals'] = ['Fake news', 'Imposter site']
    return default

filecolumns = {
    'cbsnews': default_mapping(),
    'dailydot': default_mapping(),
    'fakenewswatch': fakenewswatch_mapping(),
    'newrepublic': default_mapping(),
    'npr': default_mapping(),
    'snopes': default_mapping(),
    'thoughtco': default_mapping(),
    'usnews': usnews_mapping(),
    'politifact': politifact_mapping()
}

all_domains = []
for source, mappings in filecolumns.items():
    data = utils.read_tsv(location / 'intermediate' / '{}.tsv'.format(source))
    print(source)
    domains = [{
        'domain': el[mappings['domain_col']].lower(),
        'label': 'true' if el[mappings['label_col']] in mappings['true_vals'] else 'fake',
        'source': 'domain_list_{}'.format(source)
    } for el in data if el[mappings['label_col']] in mappings['true_vals']+mappings['fake_vals']]

    all_domains.extend(domains)

utils.write_json_with_path(all_domains, location, 'domains.json')
