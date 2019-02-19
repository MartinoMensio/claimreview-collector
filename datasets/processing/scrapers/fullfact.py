#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser

from .. import utils

facts_url = 'https://fullfact.org/'

my_path = utils.data_location / 'fullfact'

def main():
    if os.path.exists(my_path / 'fact_checking_urls.json'):
        all_statements = utils.read_json(my_path / 'fact_checking_urls.json')
    else:
        all_statements = []

    print(facts_url)
    response = requests.get(facts_url)
    if response.status_code != 200:
        print('status code', response.status_code)
        exit(0)

    soup = BeautifulSoup(response.text, 'lxml')

    for s in soup.select('div.news-feed #mostRecent li'):
        url = 'https://fullfact.org' +  s.select('a')[0]['href']
        title = s.select('a')[0].text.strip()
        date = s.select('small.date')[0].text.strip()
        date = dateparser.parse(date).isoformat()

        found = next((item for item in all_statements if (item['url'] == url and item['date'] == date)), None)
        if found:
            print('found')
            break

        all_statements.append({
            'url': url,
            'title': title,
            'date': date,
            'source': 'fullfact'
        })

    print(len(all_statements))



    utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')