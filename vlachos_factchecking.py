#!/usr/bin/env python

import utils
import claimreview
import dateparser

my_name = 'vlachos_factchecking'
location = utils.data_location / my_name

data = utils.read_tsv(location / 'source' / 'FactChecking_LTCSS2014_release.tsv')

fact_checking_urls = []
for row in data:
    original_label = row['Verdict']
    label = claimreview.simplify_label(original_label)
    date = row['Date']
    if date:
        date = dateparser.parse(date).isoformat()
    fact_checking_urls.append({
        'url': row['Link'],
        'source': my_name,
        'claim': row['Statement'],
        'label': label,
        'original_label': original_label,
        'reason': row['Notes'],
        'date': date
    })

utils.write_json_with_path(fact_checking_urls, location, 'fact_checking_urls.json')
