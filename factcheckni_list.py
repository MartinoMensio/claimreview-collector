#!/usr/bin/env python

import  utils
import claimreview

location = utils.data_location / 'factcheckni_list'

data = utils.read_tsv(location / 'source' / 'FactCheckNI Articles - OU Research - Sheet1.tsv')

labeled_urls = [{'url': row['Claim URL'], 'label': claimreview.simplify_label(row['Label']), 'source': 'factcheckni_list'} for row in data]
labeled_urls = [el for el in labeled_urls if el['label']]

rebuttals = {row['Claim URL']: {row['Article URL']: ['factcheckni_list']} for row in data}

utils.write_json_with_path(labeled_urls, location, 'urls.json')
utils.write_json_with_path(rebuttals, location, 'rebuttals.json')
