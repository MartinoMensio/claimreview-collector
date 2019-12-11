#!/usr/bin/env python

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool

from . import Scraper
from ..processing import utils
from ..processing import claimreview
from ..processing import database_builder

LIST_URL = 'https://www.factcheck.org/page/{}/'

class FactCheckOrgScraper(Scraper):
    def __init__(self):
        self.id = 'factcheck_org'
        Scraper.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = retrieve_factchecking_urls(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        with ThreadPool(8) as pool:
            urls = [r['url'] for r in all_reviews]
            for one_result in tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls), total=len(urls)):
                url_fixed, cr = one_result
                claim_reviews.extend(cr)
        # for r in tqdm(all_reviews):
        #     url_fixed, cr = claimreview.retrieve_claimreview(r['url'])
        #     claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)

def retrieve_factchecking_urls(self_id):
    page = 1
    all_statements = []
    first = True
    while True:
        url = LIST_URL.format(page)
        print(url)
        response = requests.get(url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break

        soup = BeautifulSoup(response.text, 'lxml')

        assessments = []
        for s in soup.select('main#main article'):
            link = s.select('h3.entry-title a')[0]['href']
            title = s.select('h3.entry-title a')[0].text.strip()
            subtitle = s.select('div.entry-content p')[0].text.strip()
            date = s.select('header.entry-header div.entry-meta')[0].text.strip()


            assessments.append({
                'url': link,
                'title': title,
                'subtitle': subtitle,
                'date': date
            })

        all_statements.extend(assessments)
        print(len(all_statements))
        database_builder.save_original_data(self_id, assessments, clean=first)
        first = False
        page += 1
    return all_statements

def main():
    scraper = FactCheckOrgScraper()
    scraper.scrape()

if __name__ == "__main__":
    main()