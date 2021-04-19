import csv
import os
import json
import sys
import itertools
import hashlib
import re
import tldextract
from pathlib import Path
from urllib.parse import urlparse

csv.field_size_limit(sys.maxsize)

# default value

def read_json(input_path):
    """read json from file"""
    with open(input_path) as f:
        return json.load(f)

def read_tsv(input_path, with_header=True, delimiter='\t'):
    results = []
    with open(input_path) as f:
        if with_header:
            reader = csv.DictReader(f, delimiter=delimiter)
        else:
            reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            results.append(row)
    return results

def write_json_with_path(content, path, filename, indent=2):
    """dump to json file, creating folder if necessary"""
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(path / filename, 'w') as f:
        json.dump(content, f, indent=indent)

def write_file_with_path(content, path, filename):
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(path / filename, 'w') as f:
        f.write(content)

def get_url_domain(url, only_tld=True):
    """Returns the domain of the URL
    
    The parameter `only_tld` allows to retrieve only the top domain (e.g. `foo.bbc.co.uk` becomes `bbc.co.uk`)"""
    if not url:
        return ''
    ext = tldextract.extract(url)
    if not only_tld:
        result = '.'.join(part for part in ext if part)
    else:
        result = '.'.join([ext.domain, ext.suffix])
    if result.startswith('www.'):
            # sometimes the www is there, sometimes not
            result = result[4:]
    return result.lower()

def print_stats(data):
    by_label_fn = lambda el: el[1]['label']
    by_label = itertools.groupby(sorted(data.items(), key=by_label_fn), key=by_label_fn)
    print({k: len(list(v)) for k,v in by_label}, 'total', len(data))

def identifier_from_url_or_domain(element, key):
    selected_property = element[key]
    if key == 'domain':
        if selected_property.endswith('/'):
            # only example is anews24.org/
            selected_property = selected_property[:-1]
    return selected_property

def aggregate(data_list, key='url'):
    """returns a dict, grouping the data by the key (url/domain)"""
    by_key_fn = lambda el: identifier_from_url_or_domain(el, key)
    by_key = {k: list(v) for k,v in itertools.groupby(sorted(data_list, key=by_key_fn), key=by_key_fn)}
    agree = {}
    not_agree = {}
    for k, k_group in by_key.items():
        by_label_fn = lambda el: el['label']
        by_label = {k: [el['source'] for el in v] for k,v in itertools.groupby(sorted(k_group, key=by_label_fn), key=by_label_fn)}
        if len(by_label.keys()) == 1:
            # all agree
            label = next(iter(by_label.keys()))
            agree[k] = {'label': label, 'sources': by_label[label]}
        else:
            not_agree[k] = by_label
    print(not_agree)
    return agree

def compute_by_domain(url_based_data, decision_mode='all_agree'):
    by_domain_fn = lambda el: get_url_domain(el['url'])
    by_domain = {k: list(v) for k,v in itertools.groupby(sorted(url_based_data, key=by_domain_fn), key=by_domain_fn)}

    result = []
    if decision_mode == 'all_agree':
        for k, v in by_domain.items():
            label_set = set([el['label'] for el in v])
            if len(label_set) != 1:
                print('non unique', k, label_set)
            else:
                label = label_set.pop()
                result.append({
                    'domain': k,
                    'label': label,
                    'source': v[0]['source']
                })
    else:
        raise ValueError('decision_mode not supported')

    return result

def string_to_md5(string):
    return hashlib.md5(string.encode()).hexdigest()

def read_sources():
    path = Path(os.path.dirname(os.path.realpath(__file__))) / 'sources.json'
    return read_json(path)

relationships_default_confidences = {
    'publishes': 1.0,
    'redirects': 1.0,
    'published_by': 0.5,
    'reviews': 1.0
}
