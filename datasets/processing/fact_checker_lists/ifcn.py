#!/usr/bin/env python

"""The fact chekers have domains that are good (if they are valid members of IFCN)"""

from .. import utils

my_path = utils.data_location / 'ifcn'

def main():
    data = utils.read_json(my_path / 'source'/ 'ifcn.json')

    domains = []

    for k, fc in data.items():
        properties = fc.get('properties', {})
        if properties.get('belongs_to_ifcn') and properties.get('valid'):
            domain = utils.get_url_domain(fc['url'])
            domains.append({
                'domain': domain,
                'label': 'true',
                'source': 'ifcn'
            })
        fc['id'] = k
        fc['belongs_to_ifcn'] = fc['properties']['belongs_to_ifcn']
        fc['valid'] = fc['properties'].get('valid', False)
        fc['uses_claimreview'] = fc['properties']['uses_claimreview']
        fc['source'] = 'ifcn'
        fc['domain'] = domain

    fact_checkers = [el for el in data.values()]

    utils.write_json_with_path(domains, my_path, 'domains.json')
    utils.write_json_with_path(fact_checkers, my_path, 'fact_checkers.json')
