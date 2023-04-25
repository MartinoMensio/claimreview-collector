#!/usr/bin/env python

import requests
import re
import os
from tqdm import tqdm
from bs4 import BeautifulSoup

from . import ScraperBase
from ...processing import utils
from ...processing import database_builder
from ...processing import claimreview

LIST_URL = "https://factcheckni.org/page/{}/"


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "factcheckni"
        self.homepage = "https://factcheckni.org/"
        self.name = "FactCheck Northern Ireland"
        self.description = "Misinformation, disinformation and rumours have the potential to spread rapidly on social media, undermining trust in public discourse and damaging social cohesion. FactCheckNI established Northern Ireland’s first and only dedicated fact-checking service."
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = retrieve(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        for r in tqdm(all_reviews):
            url_fixed, cr = claimreview.retrieve_claimreview(r["url"])
            claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)


def retrieve(self_id):
    page = 1
    go_on = True
    first = True
    all_statements = []
    while go_on:
        facts_url = LIST_URL.format(page)
        print(facts_url)
        response = requests.get(facts_url)
        if response.status_code != 200:
            print("status code", response.status_code)
            break

        soup = BeautifulSoup(response.text, "lxml")

        assessments = []
        for s in soup.select("main#main article"):
            url = s.select("h2.entry-title a")[0]["href"]
            title = s.select("h2.entry-title a")[0].text.strip()
            subtitle = s.select("div.entry-content p")[0].text.strip()
            date = s.select("header.entry-header div.entry-meta time.entry-date")[0][
                "datetime"
            ]
            # date = re.sub(r'Posted on (.+) ')

            if subtitle and subtitle.startswith("CLAIM: "):
                claim = subtitle.replace("CLAIM: ", "")
            else:
                claim = None

            found = next(
                (
                    item
                    for item in all_statements
                    if (item["url"] == url and item["date"] == date)
                ),
                None,
            )
            if found:
                print("found")
                go_on = False
                break

            assessments.append(
                {
                    "url": url,
                    "title": title,
                    "subtitle": subtitle,
                    "claim": claim,
                    "date": date,
                    "source": "factcheckni",
                }
            )
        all_statements.extend(assessments)
        print(len(all_statements))
        database_builder.save_original_data(self_id, assessments, clean=first)
        first = False
        page += 1

    return all_statements


def main():
    scraper = Scraper()
    scraper.scrape()


if __name__ == "__main__":
    main()
