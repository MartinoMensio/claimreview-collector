#!/usr/bin/env python
import os
import requests
from bs4 import BeautifulSoup

from ..processing import utils

LIST_URL = 'https://euvsdisinfo.eu/disinformation-cases/?offset={}'

my_name = 'euvsdisinfo'
my_path = utils.data_location / my_name

def get_credibility_measures(original_review):
    return {'credibility': -1.0, 'confidence': 1.0}

def create_claim_reviews(all_reviews):
    claim_reviews = []

    for review_url, review in all_reviews.items():
        claim_urls = review['claim_urls'] + review['archived_claim_urls']

        claim_review = {
            "@context": "http://schema.org",
            "@type": "ClaimReview",
            "url": review_url,
            "author": {
                "@type": "Organization",
                "name":"EU vs DISINFORMATION",
                "url":"https://euvsdisinfo.eu/",
                "sameAs": ["https://twitter.com/EUvsDisinfo", "https://www.facebook.com/EUvsDisinfo/"]
            },
            "claimReviewed": review['title'],
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": 1,
                "bestRating": 5,
                "worstRating": 1,
                "alternateName": 'misinfo'
            },
            "itemReviewed": {
                "@type": "Claim",
                "appearance": [{'@type': 'CreativeWork', 'url': u} for u in claim_urls]
            },
            'origin': 'euvsdisinfo'
        }

        claim_reviews.append(claim_review)

    utils.write_json_with_path(claim_reviews, my_path, 'claimReviews.json')
    return claim_reviews


def scrape():
    offset = 0
    if os.path.exists(my_path / 'source' / 'all_reviews.json'):
        all_reviews = utils.read_json(my_path / 'source' / 'all_reviews.json')
    else:
        all_reviews = {}
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
            if url in all_reviews:
                pass
                """
                # already found, stop now
                go_on = False
                print('already in all_reviews', url)
                break
                """
            else:
                response = requests.get(url)
                if response.status_code != 200:
                    raise ValueError(response.status_code)
                article = response.text
                soup = BeautifulSoup(article, 'lxml')

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


                all_reviews[url] = {
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
                    'source': my_name
                }

        print(len(all_reviews))
        #print(all_statements)
        offset += 10

    utils.write_json_with_path(all_reviews, my_path / 'source', 'all_reviews.json')
    return all_reviews


def main():
    all_reviews = scrape()
    create_claim_reviews(all_reviews)
