#!/usr/bin/env python

import json
import requests  # not cache manager
import os
import plac

from datetime import datetime
from collections import defaultdict

from pprint import pprint
from itertools import groupby

from . import ScraperBase
from ...processing import utils
from ...processing import claimreview
from ...processing import database_builder


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "google_factcheck_explorer"
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        res = retrieve(self.id, scraping=update)

        return res


def get_recent(self_id, lang="", offset=0, num_results=1000, query="list:recent"):
    params = {
        "hl": lang,  # the language to search
        "num_results": num_results,
        "query": query,
        "force": "false",
        "offset": offset,
    }
    # print(os.environ['GOOGLE_FACTCHECK_EXPLORER_COOKIE'])
    headers = {
        "dnt": "1",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-GB,en;q=0.9,it-IT;q=0.8,it;q=0.7,en-US;q=0.6",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://toolbox.google.com/factcheck/explorer/search/list:recent;hl=en;gl=",
        "authority": "toolbox.google.com",
        "cookie": os.environ["GOOGLE_FACTCHECK_EXPLORER_COOKIE"],
    }
    response = requests.get(
        "https://toolbox.google.com/factcheck/api/search",
        params=params,
        headers=headers,
    )
    if response.status_code != 200:
        raise ValueError(response.status_code)
    # print(response.text)
    # text = response.text[5:].encode().decode('utf-8', 'ignore')

    content = json.loads(response.text[5:])
    reviews = content[0][1]
    if reviews:
        database_builder.save_original_data(
            self_id, [{"raw": el} for el in reviews], clean=offset == 0
        )
    return reviews


def retrieve(self_id, scraping=False):
    if scraping:
        offset = 0
        raws = []
        while True:
            print("offset", offset)
            raw_piece = get_recent(self_id, offset=offset)
            if not raw_piece:
                break
            offset += len(raw_piece)
            raws.extend(raw_piece)
    else:
        raws = [el["raw"] for el in database_builder.get_original_data(self_id)]

    results = []
    for r in raws:
        try:
            date_published = r[0][3][0][2]
            if date_published:
                date_published = datetime.utcfromtimestamp(date_published).isoformat()
            claimReview = {
                "@context": "http://schema.org",
                "@type": "ClaimReview",
                "datePublished": date_published,
                "url": r[0][3][0][1],
                "claimReviewed": r[0][0],
                "author": {
                    "@type": "Organization",
                    "name": r[0][3][0][0][0],
                    "url": r[0][3][0][0][1],
                    # "image": ?,
                    # "sameAs": ?
                },
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": r[0][3][0][9][0]
                    if (len(r[0][3][0]) > 9 and r[0][3][0][9] and len(r[0][3][0][9]))
                    else -1,
                    "worstRating": r[0][3][0][9][1]
                    if (len(r[0][3][0]) > 9 and r[0][3][0][9] and len(r[0][3][0][9]))
                    else -1,
                    "bestRating": r[0][3][0][9][2]
                    if (len(r[0][3][0]) > 9 and r[0][3][0][9] and len(r[0][3][0][9]))
                    else -1,
                    "alternateName": r[0][3][0][3],
                    # "image": ?,
                },
                "itemReviewed": {
                    "@type": "CreativeWork",
                    "author": {
                        "@type": "Person",
                        "name": r[0][1][0],
                        "sameAs": r[0][4][0][1] if len(r[0][4]) else None,
                    }
                    if len(r[0][1])
                    else {},
                    "url": r[0][10],
                }
                #'claim_author': r[0][1][0] if len(r[0][1]) else None,
                #'id': r[0][2],
                #'review_author': r[0][3][0][0][0],
                #'review_title': r[0][3][0][8],
                #'claim_url': r[0][4][0][1] if len(r[0][4]) else None
            }
            appearance = r[0][1][2]
            firstAppearance = len(r[0]) > 13 and r[0][13]
            if appearance:
                claimReview["itemReviewed"]["appearance"] = [
                    {"url": u} for u in appearance
                ]
            if firstAppearance:
                claimReview["itemReviewed"]["firstAppearance"] = {
                    "type": "CreativeWork",
                    "url": firstAppearance,
                }
            results.append(claimReview)
        except IndexError as e:
            print(json.dumps(r))
            raise (e)

    database_builder.add_ClaimReviews(self_id, results)
    return results


def main(update=True):
    scraper = Scraper()
    scraper.scrape(update=update)


if __name__ == "__main__":
    main()
