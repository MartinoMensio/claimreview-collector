#!/usr/bin/env python

import utils
import requests
from bs4 import BeautifulSoup

LIST_URL = 'https://www.weeklystandard.com/tag/tws-fact-check'

my_path = utils.data_location / 'weeklystandard'

headers = {
    'user-agent': 'ozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
}

page = 1
all_statements = []
next_page_url = LIST_URL
while True:
    url = next_page_url
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print('status code', response.status_code)
        break


    soup = BeautifulSoup(response.text, 'lxml')
    next_page_url = soup.select('div.LoadMoreList ul[data-next-page]')
    if next_page_url:
        next_page_url = next_page_url[0]['data-next-page']
        if next_page_url:
            next_page_url = 'https://www.weeklystandard.com' + next_page_url
    if not next_page_url:
        print('no next page')
        break

    for s in soup.select('li h3.HeroTextBelowPromo-title'):
        link = s.select('a.Link')[0]['href']
        title = s.select('a.Link')[0].text.strip()


        all_statements.append({
            'link': link,
            'title': title
        })

    print(len(all_statements))



utils.write_json_with_path(all_statements, my_path, 'statements.json')