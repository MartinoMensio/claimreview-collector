#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser
import tqdm
from multiprocessing.pool import ThreadPool

from . import ScraperBase
from ...processing import utils, database_builder, claimreview

LIST_URL = 'https://www.snopes.com/fact-check/page/{}/'

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'snopes'
        self.homepage = 'https://www.snopes.com/fact-check/'
        self.name = 'Snopes'
        self.description = 'Snopes got its start in 1994, investigating urban legends, hoaxes, and folklore. Founder David Mikkelson, later joined by his wife, was publishing online before most people were connected to the internet. As demand for reliable fact checks grew, so did Snopes. Now it’s the oldest and largest fact-checking site online, widely regarded by journalists, folklorists, and readers as an invaluable research companion.'
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
    # if os.path.exists(my_path / 'fact_checking_urls.json'):
    #     all_statements = utils.read_json(my_path / 'fact_checking_urls.json')
    # else:
    #     all_statements = []
    all_statements = []
    go_on = True
    while go_on:
        facts_url = LIST_URL.format(page)
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break
        #print(response.text)
        soup = BeautifulSoup(response.text, 'lxml')

        # TODO selector is broken!!!
        for s in soup.select('main.base-main article.media-wrapper'):
            url = s.select_one('a.fact_check')['href']
            title = s.select_one('h5.title').text.strip()
            subtitle = s.select('p.subtitle')
            if subtitle:
                subtitle = subtitle[0].text.strip()
            else:
                subtitle = None
            date = s.select('span.date')
            if date:
                date = date[0].text.strip()
                date = dateparser.parse(date).isoformat()
            else:
                date = None

            found = next((item for item in all_statements if (item['url'] == url and item['date'] == date)), None)
            if found:
                print('found')
                go_on = False
                break

            all_statements.append({
                'url': url,
                'title': title,
                'subtitle': subtitle,
                'date': date,
                'source': 'snopes'
            })

        print(len(all_statements))
        page += 1


    database_builder.save_original_data(self_id, all_statements)
    return all_statements


def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()
