#!/usr/bin/env python

import re
import itertools

from .. import utils
from .. import claimreview

subfolder = utils.data_location / 'pontes_fakenewssample'

def clean_url(url):
    url = re.sub(r'&(amp;)+', '&', url)
    return url

def main():
    data = utils.read_tsv(subfolder / 'source' / 'resized_v2.csv', delimiter=',')

    print(len(data))
    print('loaded data')
    types = set([el['type'] for el in data])
    print(types)
    urls = [{'url': clean_url(el['url']), 'label': claimreview.simplify_label(el['type']), 'source': 'pontes_fakenewssample'} for el in data if el['type']]
    urls = [el for el in urls if el['label']]

    domains = [{'domain': el['domain'], 'label': claimreview.simplify_label(el['type']), 'source': 'pontes_fakenewssample'} for el in data if el['type']]
    domains = [el for el in domains if el['label']]
    #domains = {el['domain']: el for el in domains} # without different label check
    domains = {k: set([l['label'] for l in g]) for k, g in itertools.groupby(sorted(domains, key=lambda el: el['domain']), key=lambda el: el['domain'])}
    for d, values in domains.items():
        if len(values) > 1:
            print(values)
            raise ValueError('different labels')
    domains = [{'domain': k, 'label': el.pop(), 'source': 'pontes_fakenewssample'} for k, el in domains.items()]

    utils.write_json_with_path(urls, subfolder, 'urls.json')
    del data

    by_domain = utils.compute_by_domain(urls)

    utils.write_json_with_path(domains, subfolder, 'domains.json')
