#!/usr/bin/env python

import utils
import requests
import re
from bs4 import BeautifulSoup

LIST_URL = 'https://leadstories.com/cgi-bin/mt/mt-search.cgi?search=&IncludeBlogs=1&blog_id=1&archive_type=Index&limit=20&page={}#mostrecent'

my_path = utils.data_location / 'leadstories'

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
    current_page = soup.select('a.is_current')
    if not current_page:
        break

    for s in soup.select('li article'):
        link = s.select('h1 a')[0]['href']
        title = s.select('h1 a')[0].text.strip()
        subtitle = s.select('div.e_descr')[0].text.strip()
        date = s.select('ul.e_data_list li ')[0].text.strip()
        date = re.sub(r'.*"([^]]+)".*', r'\1', date)


        all_statements.append({
            'link': link,
            'title': title,
            'subtitle': subtitle,
            'date': date
        })

    print(len(all_statements))
    page += 1




utils.write_json_with_path(all_statements, my_path, 'statements.json')