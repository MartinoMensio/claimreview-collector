#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser
from tqdm import tqdm

from ..processing import utils
from ..processing import claimreview

facts_url = 'https://fullfact.org/'

my_path = utils.data_location / 'fullfact'


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


def scrape_fb_3rd_party():
    """The page https://fullfact.org/online/ contains all the debunks published for the Facebook 3rd party fact-checking"""
    page = 1
    debunks = {}
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
            debunks[url] = a

        page += 1

    print('online 3rd party', len(debunks))
    return debunks


def scrape_latest():
    if os.path.exists(my_path / 'source' / 'latest.json'):
        all_statements = utils.read_json(my_path / 'source' / 'latest.json')
    else:
        all_statements = {}

    print(facts_url)
    response = requests.get(facts_url)
    if response.status_code != 200:
        print('status code', response.status_code)
        exit(0)

    soup = BeautifulSoup(response.text, 'lxml')

    articles = feed_selector(soup.select_one('div.news-feed #mostRecent'))
    for a in articles:
        url = a['url']
        all_statements[url] = a

    print('latest', len(all_statements))
    utils.write_json_with_path(all_statements, my_path / 'source', 'latest.json')

    return all_statements

def deep_scrape():
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

    utils.write_json_with_path(result, my_path / 'source', 'deep_scrape.json')
    return result



def scrape_all():
    online_3rd = scrape_fb_3rd_party()
    latest = scrape_latest()
    deep = deep_scrape()
    all_debunks = {**online_3rd, **latest, **deep}
    print('total articles', len(all_debunks))

    utils.write_json_with_path(all_debunks, my_path / 'source', 'all_debunks.json')
    return all_debunks

def get_claimreviews():
    debunks = utils.read_json(my_path / 'source' / 'all_debunks.json')

    all_claim_reviews = []
    for debunk in tqdm(debunks.values()):
        url = debunk['url']
        claim_reviews = claimreview.get_claimreview_from_factcheckers(url)
        #print(type(claim_review), claim_review)
        all_claim_reviews.extend(claim_reviews)
    utils.write_json_with_path(all_claim_reviews, my_path, 'claimReviews.json')

    print(len(all_claim_reviews))
    return all_claim_reviews


def main():
    scrape_all()
    get_claimreviews()