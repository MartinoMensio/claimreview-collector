#!/usr/bin/env python

"""The fact chekers have domains that are good (if they are valid members of IFCN)"""

import utils

my_path = utils.data_location / 'ifcn'
sources = utils.read_json('sources.json')

domains = []

for fc in sources['fact_checkers'].values():
    properties = fc.get('properties', {})
    if properties.get('belongs_to_ifcn') and properties.get('valid'):
        domain = utils.get_url_domain(fc['url'])
        domains.append({
            'domain': domain,
            'label': 'true',
            'source': 'ifcn'
        })

utils.write_json_with_path(domains, my_path, 'domains.json')
