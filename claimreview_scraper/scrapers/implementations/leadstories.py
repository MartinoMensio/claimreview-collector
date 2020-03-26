#!/usr/bin/env python

import requests
import re
import os
from bs4 import BeautifulSoup
import tqdm
from multiprocessing.pool import ThreadPool

from .. import ScraperBase
from ...processing import utils
from ...processing import claimreview
from ...processing import database_builder

LIST_URL = 'https://leadstories.com/cgi-bin/mt/mt-search.cgi?search=&IncludeBlogs=1&blog_id=1&archive_type=Index&limit=20&page={}#mostrecent'


labels_in_title = [
    'Old Fake News: ',
    'Fake News: ',
    'Hoax Alert: '
]

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'leadstories'
        self.homepage = 'https://leadstories.com/'
        self.name = 'Lead Stories'
        self.description = '''Lead Stories is an innovative fact checking and debunking website at the intersection of big data and journalism that launched in 2015. Our editorial team used the technology provided by Trendolizer™ (patent pending) to quickly find the most trending content on the internet to write about but our mantra has always been "Just Because It's Trending Doesn't Mean It's True."'''
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
    page = 1
    
    already_saved = {el['url']: el for el in database_builder.get_original_data(self_id)}
    found_consecutively = 0
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
            if found_consecutively >= 10:
                # this is the moment to stop. We already retrieved from now on
                print(f'Interrupting after finding {found_consecutively} elements already stored')
                go_on = False
                break

            url = s.select('h1 a')[0]['href']

            if url in already_saved:
                found_consecutively += 1
                new_item = already_saved[url]
            else:
                found_consecutively = 0

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

                new_item = {
                    'url': url,
                    'title': title,
                    'subtitle': subtitle,
                    'label': label,
                    'date': date,
                    'source': 'leadstories'
                }
                already_saved[url] = new_item

        print(len(already_saved.keys()))
        page += 1

    all_statements = list(already_saved.values())
    database_builder.save_original_data(self_id, all_statements)
    return all_statements


def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()
