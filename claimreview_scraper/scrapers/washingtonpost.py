#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup

from ..processing import utils

LIST_URL = 'https://www.factcheck.org/page/{}/'

my_path = utils.data_location / 'washingtonpost'

page = 1
all_statements = []
while True:
    url = LIST_URL.format(page)
    print(url)
    response = requests.get(url)
    if response.status_code != 200:
        print('status code', response.status_code)
        break

    soup = BeautifulSoup(response.text, 'lxml')

    for s in soup.select('main#main article'):
        link = s.select('h3.entry-title a')[0]['href']
        title = s.select('h3.entry-title a')[0].text.strip()
        subtitle = s.select('div.entry-content p')[0].text.strip()
        date = s.select('header.entry-header div.entry-meta')[0].text.strip()


        all_statements.append({
            'link': link,
            'title': title,
            'subtitle': subtitle,
            'date': date
        })

    print(len(all_statements))
    page += 1



utils.write_json_with_path(all_statements, my_path, 'statements.json')