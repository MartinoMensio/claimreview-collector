#!/usr/bin/env python

import utils
import requests
from bs4 import BeautifulSoup

import dateparser

facts_url = 'https://fullfact.org/'

my_path = utils.data_location / 'fullfact'

all_statements = []

print(facts_url)
response = requests.get(facts_url)
if response.status_code != 200:
    print('status code', response.status_code)
    exit(0)

soup = BeautifulSoup(response.text, 'lxml')

for s in soup.select('div.news-feed #mostRecent li'):
    url = s.select('a')[0]['href']
    title = s.select('a')[0].text.strip()
    date = s.select('small.date')[0].text.strip()
    date = dateparser.parse(date).isoformat()


    all_statements.append({
        'url': 'https://fullfact.org' + url,
        'title': title,
        'date': date,
        'source': 'fullfact'
    })

print(len(all_statements))



utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')