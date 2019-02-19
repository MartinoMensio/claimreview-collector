#!/usr/bin/env python

import requests
import glob
import re
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from lxml import etree
import urllib.parse as urlparse
from bs4 import BeautifulSoup
import html.parser as htmlparser
parser = htmlparser.HTMLParser()

from .. import utils
from .. import claimreview

folder = utils.data_location / 'buzzface'
source_file = folder / 'source' / 'facebook-fact-check.tab'

def main():
    source_data = utils.read_tsv(source_file)

    data = {el['post_id']: {'url': el['Post URL'], 'label': el['Rating']} for el in source_data if el['Post Type'] == 'link'}
    # TODO should filter there the interesting classes?

    print(len(data))

    results = []

    # download the facebook page
    for id, el in data.items():
        # add the facebook URL to the output urls
        label_binary = claimreview.simplify_label(el['label'])
        if label_binary:
            results.append({'url': el['url'], 'label': label_binary, 'source': 'buzzface'})
        file_path = folder / 'intermediate' / '{}.html'.format(id)
        if not os.path.isfile(file_path):
            response = requests.get(el['url'])
            utils.write_file_with_path(response.text, folder / 'intermediate', '{}.html'.format(id))


    unfiltered = []

    for file_location in glob.glob(str(folder / 'intermediate/*.html')):
        #print(file_location)
        with open(file_location) as f:
            #tree = ET.parse(f)
            #soup = BeautifulSoup(f, 'html.parser')
            #tree = etree.parse(f, etree.HTMLParser())
            string = f.read()

        #root = tree.getroot()
        #matches = root.findall('a[@tabindex="-1" and target="_blank"]')
        #matches = soup.find_all('a', attrs={'tabindex': '-1', 'target': '_blank'})
        #matches = tree.xpath('a')
        # look for the <a> with tabindex="-1" target="_blank"
        fb_urls = re.findall(r'<a\shref="([^>]*)" tabindex="-1" target="_blank"', string)
        real_urls = [urlparse.parse_qs(urlparse.urlparse(u).query)['u'] for u in fb_urls]
        unique = {u for sublist in real_urls for u in sublist}
        #print(unique)
        if len(unique) != 1:
            print(file_location, unique)
            continue
        id = file_location.split('/')[-1].split('.')[0]
        url = unique.pop()
        label = data[id]['label']
        label_binary = claimreview.simplify_label(label)
        unfiltered.append({'url': url, 'label': label, 'source': 'buzzface'})
        if label_binary:
            results.append({'url': url, 'label': label_binary, 'source': 'buzzface'})

    utils.write_json_with_path(unfiltered, folder / 'intermediate', 'unfiltered.json')
    utils.write_json_with_path(results, folder, 'urls.json')

    by_domain = utils.compute_by_domain(results)
    utils.write_json_with_path(by_domain, folder, 'domains.json')
