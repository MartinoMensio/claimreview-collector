#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser
from tqdm import tqdm

from ..processing import utils, claimreview

my_path = utils.data_location / 'istinomer'

def get_urls():
    urls = []
    facts_url = 'https://www.istinomer.rs/pregled_ocena_po_tipu'
    print(facts_url)
    data = {
        'ocena[page]': 1,
        'ocena[per_page]': 1000,
        'ocena[tip_ocena][]': 3 # type 3 means "truthfulness ratings", the only ones with a claimReview
    }
    response = requests.post(facts_url, data=data)
    if response.status_code != 200:
        print('status code', response.status_code)
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')

    for s in soup.select('div.item'):
        url_relative = s.select_one('h2 a')['href']
        url = f'https://www.istinomer.rs/{url_relative}'


        urls.append(url)
    # the terminate condition is when it replies again with the first page

    print(len(urls))

    utils.write_json_with_path(urls, my_path / 'source', 'urls.json')
    return urls

def get_claim_reviews(all_urls):
    all_claim_reviews = []
    for u in tqdm(all_urls):
        claim_reviews = claimreview.get_claimreview_from_factcheckers(u)
        all_claim_reviews.extend(claim_reviews)

    utils.write_json_with_path(all_claim_reviews, my_path, 'claimReviews.json')
    return all_claim_reviews

def check():
    claim_reviews = utils.read_json(my_path / 'claimReviews.json')
    from ..processing import database_builder
    for cr in claim_reviews:
        print(type(cr))
        print(cr)
        database_builder.claimReviews_collection.insert_one(cr)

def main():
    urls = get_urls()
    get_claim_reviews(urls)
    #check()

if __name__ == "__main__":
    main()
