#!/usr/bin/env python
import os
import requests
from bs4 import BeautifulSoup

from ..processing import utils
from ..processing import cache_manager

LIST_URL = 'https://euvsdisinfo.eu/disinformation-cases/?offset={}'

my_path = utils.data_location / 'euvsdisinfo'

def main():
    offset = 0
    if os.path.exists(my_path / 'fact_checking_urls.json'):
        all_statements = utils.read_json(my_path / 'fact_checking_urls.json')
    else:
        all_statements = []
    go_on = True
    while go_on:
        facts_url = LIST_URL.format(offset)
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break

        soup = BeautifulSoup(response.text, 'lxml')

        articles = soup.select('div.disinfo-db-post ')
        if not articles:
            go_on = False
            break
        for s in articles:
            url = s.select('a')[0]['href']
            title = s.select('div.cell-title')[0].text.strip()
            date = s.select('div.disinfo-db-date')[0].text.strip()
            #outlets = s.select('data-column="Outlets"')[0].text.strip()
            country = s.select('div.cell-country')[0].text.strip()
            #date = re.sub(r'Posted on (.+) ')

            response_article = cache_manager.get(url)
            soup = BeautifulSoup(response_article, 'lxml')

            shortlink = soup.select_one('link[rel="shortlink"]')['href']

            details = soup.select('div.report-meta-item')
            for d in details:
                if 'Reported in:' in d.text:
                    issue_id = d.text.replace('Reported in:', '').replace('Issue', '').strip()
                elif 'Language:' in d.text:
                    language = d.text.replace('Language:', '').strip()
                elif 'Keywords:' in d.text:
                    keywords = d.text.replace('Keywords:', '').strip()

            report_summary = soup.select_one('div.report-summary-text').text.strip()

            claim_urls_all = soup.select('div.report-disinfo-link')

            claim_urls = claim_urls_all[0].select('a')
            claim_urls = [el['href'] for el in claim_urls]
            if len(claim_urls_all) > 1:
                archived_claim_urls = claim_urls_all[1].select('a')
                archived_claim_urls = [el['href'] for el in archived_claim_urls]
            else:
                archived_claim_urls = []

            disproof = soup.select_one('div.report-disproof-text').text.strip()


            all_statements.append({
                'url': url,
                'title': title,
                'date': date,
                'country': country,
                'shortlink': shortlink,
                'issue_id': issue_id,
                'language': language,
                'keywords': keywords,
                'summary': report_summary,
                'claim_urls': claim_urls,
                'archived_claim_urls': archived_claim_urls,
                'disproof': disproof,
                'source': 'euvsdisinfo'
            })

        print(len(all_statements))
        #print(all_statements)
        offset += 10



    utils.write_json_with_path(all_statements, my_path, 'fact_checking_urls.json')
