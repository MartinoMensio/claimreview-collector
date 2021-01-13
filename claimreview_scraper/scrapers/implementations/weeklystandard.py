#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool
import tqdm

from . import ScraperBase
from ...processing import utils, claimreview, database_builder

# WeeklyStandard fact-check is https://www.washingtonexaminer.com/

LIST_URL = 'https://www.washingtonexaminer.com/tag/tws-fact-check'

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'weeklystandard'
        self.homepage = 'https://www.washingtonexaminer.com/'
        self.name = 'Washington Examiner'
        self.description = '''The Washington Examiner brings the best in breaking news and analysis on politics. With in-depth news coverage, diligent investigative reporting and thoughtful commentary, we'll make sure you're always in the know about Washington's latest exploits'''
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = get_all_articles_url(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        with ThreadPool(8) as pool:
            urls = [r['url'] for r in all_reviews]
            for one_result in tqdm.tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls), total=len(urls)):
                url_fixed, cr = one_result
                if not cr:
                    print('no claimReview from', url_fixed)
                else:
                    claim_reviews.extend(cr)
        # for r in tqdm(all_reviews):
        #     url_fixed, cr = claimreview.retrieve_claimreview(r['url'])
        #     claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)

headers = {
    'user-agent': 'ozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
}

def get_all_articles_url(self_id):
    page = 1
    next_page_url = LIST_URL
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
        next_page_url = soup.select_one('li.ColumnList-nextPage a').get('href')
        if next_page_url:
            next_page_url = 'https://www.washingtonexaminer.com' + next_page_url
        if not next_page_url:
            print('no next page')
            break

        for s in soup.select('ul.ThumbnailAuthorDateList-items li div.ThumbnailAuthorDatePromo-info'):
            url = s.select_one('a.Link')['href']
            title = s.select_one('a.Link').text.strip()
            # print(url)

            # found = next((item for item in all_statements if (item['url'] == url and item['title'] == title)), None)
            # if found:
            #     print('found')
            #     go_on = False
            #     break

            all_statements.append({
                'url': url,
                'title': title,
                'source': 'weeklystandard'
            })

        print(len(all_statements))

    database_builder.save_original_data(self_id, all_statements)
    return all_statements



def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()