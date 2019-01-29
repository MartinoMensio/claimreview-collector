#!/usr/bin/env python

import utils
import requests
from bs4 import BeautifulSoup

LIST_URL = 'https://www.snopes.com/fact-check/page/{}/'

my_path = utils.data_location / 'snopes'

page = 1
all_statements = []
while True:
    url = LIST_URL.format(page)
    print(url)
    response = requests.get(url)
    if response.status_code != 200:
        print('status code', response.status_code)
        break
    #print(response.text)
    soup = BeautifulSoup(response.text, 'lxml')

    for s in soup.select('main.main article.list-group-item'):
        link = s.select('a.fact_check')[0]['href']
        title = s.select('h2.card-title')[0].text.strip()
        subtitle = s.select('p.card-subtitle')[0].text.strip()
        date = s.select('p.card-subtitle span.date')[0].text.strip()

        all_statements.append({
            'link': link,
            'title': title,
            'subtitle': subtitle,
            'date': date
        })

    page += 1
    print(len(all_statements))


utils.write_json_with_path(all_statements, my_path, 'statements.json')