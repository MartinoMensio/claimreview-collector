#!/usr/bin/env python
import os
import requests
from bs4 import BeautifulSoup

from .. import ScraperBase
from ...processing import database_builder
from ...processing import utils

LIST_URL = 'https://euvsdisinfo.eu/disinformation-cases/?offset={}'

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'euvsdisinfo'
        self.homepage = 'https://euvsdisinfo.eu/disinformation-cases/'
        self.name = 'EU vs Disinfo - Disinfo database'
        self.description = 'EUvsDisinfo is the flagship project of the European External Action Service’s East StratCom Task Force. It was established in 2015 to better forecast, address, and respond to the Russian Federation’s ongoing disinformation campaigns affecting the European Union, its Member States, and countries in the shared neighbourhood.\n EUvsDisinfo’s core objective is to increase public awareness and understanding of the Kremlin’s disinformation operations, and to help citizens in Europe and beyond develop resistance to digital information and media manipulation.'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        all_reviews = retrieve(self.id)
        claim_reviews = create_claim_reviews(all_reviews)
        database_builder.add_ClaimReviews(self.id, claim_reviews)


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
                "alternateName": 'disinfo'
            },
            "itemReviewed": {
                "@type": "Claim",
                "appearance": [{'@type': 'CreativeWork', 'url': u} for u in claim_urls]
            },
            'origin': 'euvsdisinfo'
        }

        claim_reviews.append(claim_review)

    return claim_reviews


def retrieve(self_id):
    offset = 0
    all_reviews = {el['url']: el for el in database_builder.get_original_data(self_id)}
    go_on = True
    first = True
    found_consecutively = 0 # we will stop after a number of matches without interruption (next iterations)
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
            if found_consecutively >= 10:
                # this is the moment to stop. We already retrieved from now on
                print(f'Interrupting after finding {found_consecutively} elements already stored')
                go_on = False
                break
            url = s.select('a')[0]['href']
            title = s.select('div.cell-title')[0].text.strip()
            date = s.select('div.disinfo-db-date')[0].text.strip()
            #outlets = s.select('data-column="Outlets"')[0].text.strip()
            country = s.select('div.cell-country')[0].text.strip()
            if url in all_reviews:
                found_consecutively += 1
                continue
            else:
                found_consecutively = 0
                response = requests.get(url)
                if response.status_code != 200:
                    raise ValueError(response.status_code)
                article = response.text
                soup = BeautifulSoup(article, 'lxml')

                shortlink = soup.select_one('link[rel="shortlink"]')['href']

                details = soup.select('ul.b-catalog__repwidget-list li')
                for d in details:
                    if 'Reported in:' in d.text:
                        issue_id = d.text.replace('Reported in:', '').replace('Issue', '').strip()
                    elif 'Language/target audience:' in d.text:
                        language = d.text.replace('Language/target audience:', '').strip()
                    elif 'Keywords:' in d.text:
                        keywords = d.text.replace('Keywords:', '').strip()

                report_summary = soup.select_one('div.b-report__summary-text').text.strip()

                claim_urls_all = soup.select('div.b-catalog__repwidget-source')
                if claim_urls_all:
                    # old way of presenting (view original, view archived)
                    claim_urls = claim_urls_all[0].select('a')
                    claim_urls = [el['href'] for el in claim_urls]
                    if len(claim_urls_all) > 1:
                        archived_claim_urls = claim_urls_all[1].select('a')
                        archived_claim_urls = [el['href'] for el in archived_claim_urls]
                    else:
                        archived_claim_urls = []
                else:
                    # new way of presenting (original (archived))
                    claim_urls_all = soup.select('div.b-catalog__link')
                    claim_urls = []
                    archived_claim_urls = []
                    for u in claim_urls_all:
                        links = u.select('a')
                        claim_urls.append(links[0]['href'])
                        if len(links) > 1:
                            archived_claim_urls.extend([el['href'] for el in links[1:]])

                disproof = soup.select_one('div.b-report__disproof-text').text.strip()


                new_report = {
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
                    'source': self_id
                }
                all_reviews[url] = new_report
                # clean always false, the check on duplicate is already done by the dict all_reviews
                database_builder.save_original_data(self_id, [new_report], clean=False)
                first = False

        print(len(all_reviews))
        #print(all_statements)
        offset += 10

        # if offset > 20:
        #     break

    return all_reviews


def main():
    scraper = Scraper()
    scraper.scrape()


if __name__ == "__main__":
    main()