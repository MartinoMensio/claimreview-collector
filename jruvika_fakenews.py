#!/bin/env python
from collections import defaultdict

import utils

subfolder = utils.data_location / 'jruvika_fakenews'

data = utils.read_tsv(subfolder / 'source' / 'data.csv', delimiter=',')

print(len(data))

# lots of urls are duplicated
by_url = defaultdict(set)
for el in data:
    # two rows have two different URLs each
    keys = [k.strip() for k in el['URLs'].split('; ')]
    value = 'true' if el['Label'] == '1' else 'fake'
    for k in keys:
        by_url[k].add(value)
        # be sure that when there are duplicates, the label is the same
        assert len(by_url[k]) == 1
urls = [{'url': k, 'label': v.pop(), 'source': 'jruvika_fakenews'} for k,v in by_url.items()]
#by_url = {el['URLs'].strip(): 'true' if el['Label'] == '1' else 'fake' for el in data}
#urls = [{'url': k, 'label': v, 'source': 'jruvika_fakenews'} for k,v in by_url.items()]
print('unique urls', len(urls))


utils.write_json_with_path(urls, subfolder, 'urls.json')

by_domain = utils.compute_by_domain(urls)

utils.write_json_with_path(by_domain, subfolder, 'domains.json')
