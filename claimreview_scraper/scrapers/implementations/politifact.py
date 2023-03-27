#!/usr/bin/env python

import requests
import os
from bs4 import BeautifulSoup
import dateparser
import tqdm
from multiprocessing.pool import ThreadPool

from . import ScraperBase
from ...processing import utils
from ...processing import claimreview, database_builder

LIST_URL = "https://www.politifact.com/factchecks/list/?page={}&category=truth-o-meter"
STATEMENT_SELECTOR = "article.m-statement"


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "politifact"
        self.homepage = "https://www.politifact.com/truth-o-meter/"
        self.name = "PolitiFact"
        self.description = "PolitiFact Truth-o-meter."
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = retrieve_factchecking_urls(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        with ThreadPool(8) as pool:
            urls = [r["url"] for r in all_reviews]
            for one_result in tqdm.tqdm(
                pool.imap_unordered(claimreview.retrieve_claimreview, urls),
                total=len(urls),
            ):
                url_fixed, cr = one_result
                if not cr:
                    # print('unrecovered from', url_fixed)
                    pass
                else:
                    claim_reviews.extend(cr)
        # for r in tqdm(all_reviews):
        #     url_fixed, cr = claimreview.retrieve_claimreview(r['url'])
        #     claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)


def retrieve_factchecking_urls(self_id):
    page = 1
    all_statements = []
    go_on = True
    while go_on:
        facts_url = LIST_URL.format(page)
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print("status code", response.status_code)
            break
        # print(response.text)
        soup = BeautifulSoup(response.text, "lxml")
        # page_number_real = soup.select('div.pagination span.step-links__current')[0].text
        # if str(page) not in page_number_real:
        #     print(page_number_real)
        #     break
        statements = soup.select(STATEMENT_SELECTOR)
        # print(statements)
        for s in statements:
            url = (
                "https://www.politifact.com"
                + s.select_one("div.m-statement__quote a")["href"]
            )
            claim = s.select_one("div.m-statement__quote a").text
            author = s.select_one("div.m-statement__author a").text
            label = s.select_one("div.m-statement__meter img")["alt"]
            # reason = s.select_one('div.meter p.quote')[0].text
            date = s.select_one("footer.m-statement__footer").text
            date = date.split("•")[-1]
            date = dateparser.parse(date).isoformat()

            # found = next((item for item in all_statements if (item['url'] == url and item['date'] == date)), None)
            # if found:
            #     print('found')
            #     go_on = False
            #     break

            # print(link, author, rating)
            all_statements.append(
                {
                    "url": url,
                    "claim": claim,
                    "author": author,
                    "label": claimreview.simplify_label(label),
                    "original_label": label,
                    # 'reason': reason,
                    "date": date,
                    "source": "politifact",
                }
            )

        print(len(all_statements))
        page += 1

    database_builder.save_original_data(self_id, all_statements)
    return all_statements


def main():
    scraper = Scraper()
    scraper.scrape()


if __name__ == "__main__":
    main()
