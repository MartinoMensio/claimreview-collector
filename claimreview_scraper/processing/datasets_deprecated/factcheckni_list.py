#!/usr/bin/env python

import dateparser

from .. import utils
from .. import claimreview

location = utils.data_location / 'factcheckni_list'

def main():
    data = utils.read_tsv(location / 'source' / 'FactCheckNI Articles - OU Research - Sheet1.tsv')
    # last line is totals
    data = data[:-1]

    labeled_urls = [{'url': row['Claim URL'], 'label': claimreview.simplify_label(row['Label']), 'source': 'factcheckni_list'} for row in data]
    labeled_urls = [el for el in labeled_urls if el['label']]

    rebuttals = {row['Claim URL']: {row['Article URL']: ['factcheckni_list']} for row in data}

    fact_checking_urls = []
    for row in data:
        original_label = row['Label']
        label = claimreview.simplify_label(row['Label'])
        conclusion = row['Conclusion']
        conclusion = conclusion.replace('CONCLUSION: ', '')
        date = row['Date Published']
        date = dateparser.parse(date, settings={'DATE_ORDER': 'DMY'}).isoformat()
        fact_checking_urls.append({
            'url': row['Article URL'],
            'source': 'factcheckni_list',
            'title': row['Article'],
            'claim': row['Claim'],
            'claim_url': row['Claim URL'],
            'label': label,
            'original_label': original_label,
            'reason': conclusion,
            'date': date
        })

    utils.write_json_with_path(fact_checking_urls, location, 'fact_checking_urls.json')

    utils.write_json_with_path(labeled_urls, location, 'urls.json')
    utils.write_json_with_path(rebuttals, location, 'rebuttals.json')
