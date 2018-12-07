#!/bin/env python

import  utils

location = utils.data_location / 'factcheckni_list'

data = utils.read_tsv(location / 'source' / 'FactCheckNI Articles - OU Research - Sheet1.tsv')

label_map = {
    'Accurate': 'true',
    # 'Unsubstantiated': not true nor folse, no proofs --> discard
    'Inaccurate': 'fake'
}

labeled_urls = [{'url': row['Claim URL'], 'label': label_map[row['Label']], 'source': 'factcheckni_list'} for row in data if row['Label'] in label_map]

rebuttals = {row['Claim URL']: {row['Article URL']: ['factcheckni_list']} for row in data}

utils.write_json_with_path(labeled_urls, location, 'urls.json')
utils.write_json_with_path(rebuttals, location, 'rebuttals.json')
