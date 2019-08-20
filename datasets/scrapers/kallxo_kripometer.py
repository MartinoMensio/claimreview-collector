import requests
import os
from bs4 import BeautifulSoup
import dateparser
from tqdm import tqdm

from ..processing import utils, claimreview

my_path = utils.data_location / 'kallxo_kripometer'

def get_urls():
    page = 1
    urls = []
    go_on = True
    while go_on:
        facts_url = f'https://kallxo.com/krypometer/?krypometer_paged={page}'
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print('status code', response.status_code)
            break
        #print(response.text)
        soup = BeautifulSoup(response.text, 'lxml')

        selected = soup.select('div.kryptometer_archive__round_full div.post_item')
        if not selected:
            break

        for s in selected:
            url = s.select_one('a')['href']

            urls.append(url)

        print(len(urls))
        page += 1


    utils.write_json_with_path(urls, my_path / 'source', 'urls.json')
    return urls

def get_claim_reviews(all_urls):
    claim_reviews = []
    for u in tqdm(all_urls):
        claim_review = claimreview.retrieve_claimreview(u)
        claim_reviews.extend(claim_review[1])

    utils.write_json_with_path(claim_reviews, my_path, 'claimReviews.json')
    return claim_reviews

def main():
    urls = get_urls()
    get_claim_reviews(urls)

if __name__ == "__main__":
    main()
