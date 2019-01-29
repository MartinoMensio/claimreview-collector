#!/usr/bin/env python

import utils
import requests
from bs4 import BeautifulSoup

url = 'https://fullfact.org/'

my_path = utils.data_location / 'fullfact'

all_statements = []

print(url)
response = requests.get(url)
if response.status_code != 200:
    print('status code', response.status_code)
    exit(0)

soup = BeautifulSoup(response.text, 'lxml')

for s in soup.select('div.news-feed #mostRecent li'):
    link = s.select('a')[0]['href']
    title = s.select('a')[0].text.strip()
    date = s.select('small.date')[0].text.strip()


    all_statements.append({
        'link': 'https://fullfact.org' + link,
        'title': title,
        'date': date
    })

print(len(all_statements))



utils.write_json_with_path(all_statements, my_path, 'statements.json')