#!/usr/bin/env python
import os
import requests
import pathlib
import tqdm
from bs4 import BeautifulSoup

from . import ScraperBase
from ...processing import database_builder
from ...processing import utils, claimreview, extract_claim_reviews

# https://pressgazette.co.uk/ukraine-fake-news/


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "ukrainefacts"
        self.homepage = "https://ukrainefacts.org/"
        self.name = "#UkraineFacts"
        self.description = "#UkraineFacts: fact-checking disinformation about Ukraine's invasion by the IFCN Signatories"
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        claim_reviews = retrieve(self.id)
        claim_reviews = list(claim_reviews.values())
        database_builder.add_ClaimReviews(self.id, claim_reviews)


def retrieve(self_id):
    res = requests.get("https://ukrainefacts.org/uploads/data.json")
    res.raise_for_status()

    database_builder.save_original_data(self_id, all_statements)
    return all_statements


def clean_field(field):
    return field.replace("\r", "").replace("\n", "\\n").strip()


# code to comapre this against IFCN and euvsdisinfo
import requests
from collections import defaultdict
from claimreview_collector.processing import unshortener, utils

# ifcn = utils.read_tsv('ukraine_IFCN.tsv')
# eu = utils.read_tsv('ukraine_euvsdisinfo_newlines_fixed.tsv')
# ifcn_mis_urls = set(el['misinforming_url'] for el in ifcn)
# eu_mis_urls = set(el['misinforming_url'] for el in eu)
# ifcn_rev_urls = set(el['review_url'] for el in ifcn)
# eu_rev_urls = set(el['review_url'] for el in eu)


def main(output_path="ukraine_ukrainefacts.tsv"):
    res = requests.get("https://data.maldita.es/ukrainefacts")
    res.raise_for_status()
    svitlo = res.json()
    svitlo_mis_urls = set(el["disinfoLink"] for el in svitlo if el["disinfoLink"])
    svitlo_rev_urls = set(
        occ["debunkLink"]
        for el in svitlo
        for occ in el["ocurrences"]
        if occ["debunkLink"]
    )

    svitlo_by_mis_url = defaultdict(list)
    for el in svitlo:
        if el["disinfoLink"]:
            for occ in el["ocurrences"]:
                if occ["debunkLink"]:
                    svitlo_by_mis_url[el["disinfoLink"]].append(occ["debunkLink"])

    svitlo_tsv = []
    for el in tqdm.tqdm(svitlo, desc="ukrainefacts"):
        if not el["disinfoLink"]:
            continue
        for occ in el["ocurrences"]:
            misinforming_url = clean_field(el["disinfoLink"])
            if misinforming_url and misinforming_url.startswith("http"):
                misinforming_url_full = unshortener.unshorten(misinforming_url)
                svitlo_tsv.append(
                    {
                        "misinforming_url": misinforming_url_full,
                        "misinforming_url_original": misinforming_url,
                        "misinforming_domain": utils.get_url_domain(
                            misinforming_url_full
                        ),
                        "date_published": occ["date"],
                        "n_reviews": len(svitlo_by_mis_url[el["disinfoLink"]]),
                        "review_url": clean_field(occ["debunkLink"]),
                        "label": "disinfo",
                        "original_label": None,
                        "fact_checker": occ["factchecker"],
                        "country": occ["country"]["name"],
                        "claim_text": clean_field(occ["debunkTitle"]),
                        "factcheck_language": occ["country"]["name"],
                    }
                )

    # df = pd.DataFrame(svitlo_tsv)
    # df.to_csv("ukraine_ukrainefacts.tsv", sep="\t", index=False)
    utils.write_tsv(output_path, svitlo_tsv)
    return len(svitlo_tsv)


if __name__ == "__main__":
    main()
