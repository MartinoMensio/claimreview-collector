#!/usr/bin/env python
import os
import requests
import pathlib
from bs4 import BeautifulSoup

from . import ScraperBase
from ...processing import database_builder
from ...processing import utils, claimreview, extract_claim_reviews
from ...processing import flaresolverr

LIST_URL = "https://euvsdisinfo.eu/disinformation-cases/?offset={}&per_page=100&orderby=date&order=DESC"


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "euvsdisinfo"
        self.homepage = "https://euvsdisinfo.eu/disinformation-cases/"
        self.name = "EU vs Disinfo - Disinfo database"
        self.description = "EUvsDisinfo is the flagship project of the European External Action Service’s East StratCom Task Force. It was established in 2015 to better forecast, address, and respond to the Russian Federation’s ongoing disinformation campaigns affecting the European Union, its Member States, and countries in the shared neighbourhood.\n EUvsDisinfo’s core objective is to increase public awareness and understanding of the Kremlin’s disinformation operations, and to help citizens in Europe and beyond develop resistance to digital information and media manipulation."
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        try:
            claim_reviews = retrieve(self.id)
            claim_reviews = list(claim_reviews.values())
            database_builder.add_ClaimReviews(self.id, claim_reviews)
        finally:
            # This processes everything toghether and saves json files
            extract_claim_reviews.extract_ifcn_claimreviews(
                domains=["euvsdisinfo.eu"], recollect=False, unshorten=False
            )
            pass
        # for cr in claim_reviews:
        #     del cr['_id']
        # utils.write_json_with_path(claim_reviews, pathlib.Path('data/latest'), 'euvsdisinfo.json')


def retrieve(self_id):
    offset = 0
    all_reviews = {el["url"]: el for el in database_builder.get_original_data(self_id)}
    go_on = True
    first = True
    found_consecutively = 0  # we will stop after a number of matches without interruption (next iterations)
    while go_on:
        facts_url = LIST_URL.format(offset)
        print(facts_url)
        text = flaresolverr.get_cloudflare(facts_url)

        soup = BeautifulSoup(text, "lxml")

        articles = soup.select("tr.disinfo-db-post ")
        offset_increase = len(articles)
        if not articles:
            go_on = False
            break
        for s in articles:
            if found_consecutively >= 100:
                # this is the moment to stop. We already retrieved from now on
                print(
                    f"Interrupting after finding {found_consecutively} elements already stored"
                )
                go_on = False
                break
            relative_url = s.select("a")[0]["href"]
            url = f"https://euvsdisinfo.eu{relative_url}"
            title = s.select("td.cell-title")[0].text.strip()
            date = s.select("td.disinfo-db-date")[0].text.strip()
            # outlets = s.select('data-column="Outlets"')[0].text.strip()
            country = s.select("td.cell-country")[0].text.strip()
            if url in all_reviews:
                found_consecutively += 1
                continue
            else:
                found_consecutively = 0
                article = flaresolverr.get_cloudflare(url)
                # now euvsdisinfo uses ClaimReview
                # insert manually in Cache because cloudflare does not enable this
                # print(type(article))
                database_builder.cache_put(url, article)
                url_fixed, cr = claimreview.retrieve_claimreview(url)
                # print(cr, type(cr))
                if not cr:
                    # 404 https://euvsdisinfo.eu/report/the-malm%c3%b6-police-is-flooded-with-dozens-of-unresolved-murders
                    # 404 https://euvsdisinfo.eu/report/vilnius-summit-of-eastern-partnership-as-a-formal-impulse-of-the-%d1%81oup-detat-in-ukraine
                    # 404 https://euvsdisinfo.eu/report/%d1%82here-are-many-ways-to-destroy-weak-statehood-without-military-action-the-example-of-ukraine-is-significant
                    # 404 https://euvsdisinfo.eu/report/satanists-and-transvestites-impose-their-own-life-rules-and-false-values-%e2%80%8b%e2%80%8bon-us
                    # 404 https://euvsdisinfo.eu/report/zelensky%d1%83-introduces-tax-on-war-and-coronavirus-in-ukraine
                    # 404 https://euvsdisinfo.eu/report/coe-and-eu-has-never-bear-christian-moral-values-but-the-values-%e2%80%8b%e2%80%8bof-satan
                    # 404 https://euvsdisinfo.eu/report/navalnys-allegations-on-putin-palace-are-false-and-russia-never-tried-t%ce%bf-target-him
                    # 404 https://euvsdisinfo.eu/report/%d0%b0s-long-as-the-west-exists-as-much-as-it-will-covet-the-material-resources-of-russia
                    print("ERROR: no ClaimReview at", url)
                    # raise ValueError(cr)
                else:
                    all_reviews[url] = cr
                    # clean always false, the check on duplicate is already done by the dict all_reviews
                    database_builder.save_original_data(self_id, cr, clean=False)
                first = False

        print(len(all_reviews))
        # print(all_statements)
        offset += offset_increase

        # if offset > 20:
        #     break

    return all_reviews


def main():
    scraper = Scraper()
    try:
        scraper.scrape()
    except Exception as e:
        # first time gives exception (something is wrong with dict / lists)
        print(e)
    # but second time it's ok
    scraper.scrape()


if __name__ == "__main__":
    main()
