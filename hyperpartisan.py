#!/usr/bin/env python

import glob
import xml.etree.ElementTree as ET

import utils

subfolder = utils.data_location / 'hyperpartisan'

results = []
for input_file in glob.glob(str(subfolder / 'intermediate/ground-truth-*.xml')):
    with open(input_file) as f:
        tree = ET.parse(f)
    articles = tree.getroot().findall('article')
    results.extend([{'url': el.attrib['url'], 'label': 'fake' if el.attrib['hyperpartisan'] == 'true' else 'true', 'source': 'hyperpartisan'} for el in articles])

utils.write_json_with_path(results, subfolder, 'urls.json')
utils.print_stats(results)
by_domain = utils.compute_by_domain(results)

utils.write_json_with_path(by_domain, subfolder, 'domains.json')
