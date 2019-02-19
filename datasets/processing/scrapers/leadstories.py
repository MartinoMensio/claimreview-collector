#!/usr/bin/env python

import requests
import re
import os
from bs4 import BeautifulSoup

from .. import utils
from .. import claimreview

LIST_URL = 'https://leadstories.com/cgi-bin/mt/mt-search.cgi?search=&IncludeBlogs=1&blog_id=1&archive_type=Index&limit=20&page={}#mostrecent'

my_path = utils.data_location / 'leadstories'

labels_in_title = [
    'Old Fake News: ',
    'Fake News: ',
    'Hoax Alert: '
]

def main():
    page = 1
    if os.path.exists(my_path / 'fact_checking_urls.json'):
        all_statements = utils.read_json(my_path / 'fact_checking_urls.json')
    else:
        all_statements = []
    go_on = True
    while go_on:
        facts_url = LIST_URL.format(page)
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break

        soup = BeautifulSoup(response.text, 'lxml')
        current_page = soup.select('a.is_current')
        if not current_page:
            break

        for s in soup.select('li article'):
            url = s.select('h1 a')[0]['href']
            title = s.select('h1 a')[0].text.strip()
            subtitle = s.select('div.e_descr')[0].text.strip()
            date = s.select('ul.e_data_list li ')[0].text.strip()
            date = re.sub(r'.*"([^]]+)".*', r'\1', date)

            label = None
            for l in labels_in_title:
                if title.startswith(l):
                    label = l[:-2]
                    label = claimreview.simplify_label(label)
                    break

            found = next((item for item in all_statements if (item['url'] == url and item['date'] == date)), None)
            if found:
                print('found')
                go_on = False
                break

            all_statements.append({
                'url': url,
                'title': title,
                'subtitle': subtitle,
                'label': label,
                'date': date,
                'source': 'leadstories'
            })

        print(len(all_statements))
        page += 1


    utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')