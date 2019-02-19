#!/usr/bin/env python

import glob

from .. import utils

def process_source_file(file_path, label):
    subfolder_name = file_path.split('/')[-3]
    data = utils.read_json(file_path)
    url = data.get('url', None)
    if url:
        return {'url': url, 'label': label, 'source': 'fakenewsnet_{}'.format(subfolder_name)}
    else:
        return None


location = utils.data_location / 'fakenewsnet'

def main():
    origin_folder = location / 'source' / 'Data'

    fakes_files = glob.glob(str(origin_folder / '*/FakeNewsContent/*.json'))
    trues_files = glob.glob(str(origin_folder / '*/RealNewsContent/*.json'))

    print('#fakes', len(fakes_files), '#trues', len(trues_files))
    urls = []
    for f in fakes_files:
        url = process_source_file(f, 'fake')
        if url:
            urls.append(url)
    for f in trues_files:
        url = process_source_file(f, 'true')
        if url:
            urls.append(url)

    utils.write_json_with_path(urls, location, 'urls.json')

    domains = utils.compute_by_domain(urls)
    utils.write_json_with_path(domains, location, 'domains.json')
