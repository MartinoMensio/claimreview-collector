#!/usr/bin/env python

import utils
import requests
from bs4 import BeautifulSoup

LIST_URL = 'https://www.politifact.com/truth-o-meter/statements/?page={}'
STATEMENT_SELECTOR = 'div.statement'


my_path = utils.data_location / 'politifact'


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
    page_number_real = soup.select('div.pagination span.step-links__current')[0].text
    if str(page) not in page_number_real:
        print(page_number_real)
        break
    statements = soup.select(STATEMENT_SELECTOR)
    #print(statements)
    for s in statements:
        link = s.select('p.statement__text a.link')[0]['href']
        claim = s.select('p.statement__text a.link')[0].text
        author = s.select('div.statement__source a')[0].text
        label = s.select('div.meter img')[0]['alt']
        review = s.select('div.meter p.quote')[0].text
        date = s.select('p.statement__edition span.article__meta')[0].text


        #print(link, author, rating)
        all_statements.append({
            'link': 'https://www.politifact.com/' + link,
            'claim': claim,
            'author': author,
            'label': label,
            'review': review,
            'date': date
        })
    page += 1

    print(len(all_statements))


utils.write_json_with_path(all_statements, my_path, 'statements.json')