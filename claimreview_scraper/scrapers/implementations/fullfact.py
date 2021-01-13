#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser
from tqdm import tqdm

from . import ScraperBase
from ...processing import utils
from ...processing import claimreview
from ...processing import database_builder

facts_url = 'https://fullfact.org/'

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'fullfact'
        self.homepage = 'https://fullfact.org/'
        self.name = 'Full Fact'
        self.description = 'Full Fact is a registered charity. They actively seek a diverse range of funding and are transparent about all our sources of income.'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = scrape_all(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        for r in tqdm(all_reviews):
            url_fixed, cr = claimreview.retrieve_claimreview(r['url'])
            claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)


def postlist_selector(soup):
    result = []
    articles = soup.select('div.postlist-item')
    for a in articles:
        title_el = a.select_one('h2.postlist-item-heading a')
        if not title_el:
            # the newsletter element
            continue
        url = f'https://fullfact.org{title_el["href"]}'
        subtitle = a.select_one('p')
        article = {
            'title': title_el.text.strip(),
            'url': url,
            'subtitle': subtitle.text.strip(),
            'source': 'fullfact'
        }
        result.append(article)
    return result

def feed_selector(soup):
    result = []
    if not soup:
        return []
    for s in soup.select('li'):
        url = 'https://fullfact.org' +  s.select('a')[0]['href']
        title = s.select('a')[0].text.strip()
        date = s.select('small.date')[0].text.strip()
        date = dateparser.parse(date).isoformat()

        article = {
            'url': url,
            'title': title,
            'date': date,
            'source': 'fullfact'
        }
        result.append(article)
    return result


def scrape_fb_3rd_party(self_id):
    """The page https://fullfact.org/online/ contains all the debunks published for the Facebook 3rd party fact-checking"""
    page = 1
    already_here = database_builder.get_original_data(self_id)
    debunks = {el['url']: el for el in already_here}
    while True:
        listing_page_url = f'https://fullfact.org/online/?page={page}'
        print(listing_page_url)
        response = requests.get(listing_page_url)
        if response.status_code != 200:
            print(response.status_code)
            break
        page_content = response.text
        soup = BeautifulSoup(page_content, 'lxml')
        articles = postlist_selector(soup)
        for a in articles:
            url = a['url']
            if url not in debunks:
                debunks[url] = a
                database_builder.save_original_data(self_id, [a], clean=False)

        page += 1

    print('online 3rd party', len(debunks))
    
    return debunks


def scrape_latest(self_id):
    already_here = database_builder.get_original_data(self_id)
    all_statements = {el['url']: el for el in already_here}

    print(facts_url)
    response = requests.get(facts_url)
    if response.status_code != 200:
        print('status code', response.status_code)
        exit(0)

    soup = BeautifulSoup(response.text, 'lxml')

    articles = feed_selector(soup.select_one('div.news-feed #mostRecent'))
    for a in articles:
        url = a['url']
        if url not in all_statements:
            all_statements[url] = a
            database_builder.save_original_data(self_id, [a], clean=False)

    print('latest', len(all_statements))

    return all_statements

def deep_scrape(self_id):
    already_here = database_builder.get_original_data(self_id)
    all_statements = {el['url']: el for el in already_here}

    result = {}
    # nested by category
    homepage = requests.get('https://fullfact.org/')
    if homepage.status_code != 200:
        raise ValueError(homepage.status_code)
    soup = BeautifulSoup(homepage.text, 'lxml')
    categories = soup.select('ul.nav-bar-categories li')
    for c in categories:
        category_url = f'https://fullfact.org{c.select_one("a")["href"]}'
        print(category_url)
        category = requests.get(category_url)
        if category.status_code != 200:
            raise ValueError(category.status_code)
        soup = BeautifulSoup(category.text, 'lxml')
        subcategories = soup.select('ul.debates-list li')
        for sc in subcategories:
            subcategory_url = f'https://fullfact.org{sc.select_one("a")["href"]}'
            print('   ', subcategory_url)
            subcategory = requests.get(subcategory_url)
            if subcategory.status_code != 200:
                raise ValueError(subcategory.status_code)
            soup = BeautifulSoup(subcategory.text, 'lxml')
            articles = feed_selector(soup.select_one('div.stories-feed'))
            print(len(articles))
            for a in articles:
                url = a['url']

                result[url] = a
                if url not in all_statements:
                    all_statements[url] = a
                    database_builder.save_original_data(self_id, [a], clean=False)

    return result



def scrape_all(self_id):
    online_3rd = scrape_fb_3rd_party(self_id)
    latest = scrape_latest(self_id)
    deep = deep_scrape(self_id)
    all_debunks = {**online_3rd, **latest, **deep}
    print('total articles', len(all_debunks))

    return all_debunks.values()



def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()