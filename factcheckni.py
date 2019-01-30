#!/usr/bin/env python

import utils
import requests
import re
from bs4 import BeautifulSoup

LIST_URL = 'https://factcheckni.org/page/{}/'

my_path = utils.data_location / 'factcheckni'

page = 1
all_statements = []
while True:
    facts_url = LIST_URL.format(page)
    print(facts_url)
    response = requests.get(facts_url)
    if response.status_code != 200:
        print('status code', response.status_code)
        break

    soup = BeautifulSoup(response.text, 'lxml')

    for s in soup.select('main#main article'):
        url = s.select('h2.entry-title a')[0]['href']
        title = s.select('h2.entry-title a')[0].text.strip()
        subtitle = s.select('div.entry-content p')[0].text.strip()
        date = s.select('header.entry-header div.entry-meta time.entry-date')[0]['datetime']
        #date = re.sub(r'Posted on (.+) ')

        if subtitle and subtitle.startswith('CLAIM: '):
            claim = subtitle.replace('CLAIM: ', '')
        else:
            claim = None


        all_statements.append({
            'url': url,
            'title': title,
            'subtitle': subtitle,
            'claim': claim,
            'date': date,
            'source': 'factcheckni'
        })

    print(len(all_statements))
    page += 1



utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')