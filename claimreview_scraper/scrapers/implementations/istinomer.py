#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser
from multiprocessing.pool import ThreadPool
import tqdm

from ...processing import utils, claimreview, database_builder
from .. import ScraperBase

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'istinomer'
        self.homepage = 'https://www.istinomer.rs/'
        self.name = 'Istinomer'
        self.description = 'Istinomer is a member of The Press Council and respects Serbian Journalists’ Code of Ethics'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = retrieve_factchecking_urls(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        with ThreadPool(8) as pool:
            urls = [r['url'] for r in all_reviews]
            for one_result in tqdm.tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls), total=len(urls)):
                url_fixed, cr = one_result
                claim_reviews.extend(cr)
        # for r in tqdm(all_reviews):
        #     url_fixed, cr = claimreview.retrieve_claimreview(r['url'])
        #     claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)

def retrieve_factchecking_urls(self_id):
    fc_urls = []
    facts_url_base = 'https://www.istinomer.rs/ocene/istinitost,doslednost,obecanja,sto-zelenije-to-pliva,beleznica,dnevnik-uvreda,izjave-ljubavi,zloupotreba-cinjenica,neproverivo,5-oktobar-10-godina-kasnije-izjave,drustvo,ekonomija,kultura,politika,zdravstvo/'
    # print(facts_url)
    # data = {
    #     'ocena[page]': 1,
    #     'ocena[per_page]': 1000,
    #     'ocena[tip_ocena][]': 3 # type 3 means "truthfulness ratings", the only ones with a claimReview
    # }
    page = 1
    while True:
        page_url = f'{facts_url_base}/page/{page}'
        response = requests.get(page_url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break


        soup = BeautifulSoup(response.text, 'lxml')

        for s in soup.select('article'):
            # url_relative = s.select_one('h2 a')['href']
            # url = f'https://www.istinomer.rs/{url_relative}'
            headline_el = s.select_one('h2.posttitle a')
            if not headline_el:
                title = ''
                url = s.select_one('a')['href']
                print('url', url, 'without title')
            else:
                title = headline_el.text.strip()
                url = headline_el['href']
            fc_urls.append({
                'url': url,
                'claim': title,
                # 'author': author,
                # 'label': claimreview.simplify_label(label),
                # 'original_label': label,
                # 'reason': reason,
                # 'date': date,
                'source': 'istinomer'
            })

        print('page', page, 'total collected', len(fc_urls))
        page += 1

            # urls.append(url)
    # the terminate condition is when it replies again with the first page

    print(len(fc_urls))

    database_builder.save_original_data(self_id, fc_urls)
    return fc_urls

def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()
