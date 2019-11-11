#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup

from ..processing import utils

LIST_URL = 'https://www.weeklystandard.com/tag/tws-fact-check'

my_path = utils.data_location / 'weeklystandard'

headers = {
    'user-agent': 'ozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
}

def main():
    page = 1
    next_page_url = LIST_URL
    if os.path.exists(my_path / 'fact_checking_urls.json'):
        all_statements = utils.read_json(my_path / 'fact_checking_urls.json')
    else:
        all_statements = []
    go_on = True
    while go_on:
        facts_url = next_page_url
        print(facts_url)
        response = requests.get(facts_url, headers=headers)
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
            url = s.select('a.Link')[0]['href']
            title = s.select('a.Link')[0].text.strip()

            found = next((item for item in all_statements if (item['url'] == url and item['title'] == title)), None)
            if found:
                print('found')
                go_on = False
                break

            all_statements.append({
                'url': url,
                'title': title,
                'source': 'weeklystandard'
            })

        print(len(all_statements))



    utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')