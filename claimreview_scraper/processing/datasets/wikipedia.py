#!/usr/bin/env python

from .. import utils
from .. import claimreview

location = utils.data_location / 'wikipedia'

def main():
    data = utils.read_tsv(location / 'source' / 'wikipedia.tsv')

    domains = [{'domain': el['url'], 'label': el['label'], 'source': 'wikipedia'} for el in data]

    assessments = []
    source = utils.read_sources()['wikipedia']['url']
    for d in domains:
        domain = d['domain']
        label = d['label']
        credibility = claimreview.credibility_score_from_label(label)
        assessments.append({
            'from': source,
            'to': domain,
            'link_type': 'assesses',
            'credibility': credibility,
            'confidence': 1.0,
            'generated_by': 'wikipedia',
            'original_evaluation': label
        })

    utils.write_json_with_path(assessments, location, 'domain_assessments.json')
    utils.write_json_with_path(domains, location, 'domains.json')
