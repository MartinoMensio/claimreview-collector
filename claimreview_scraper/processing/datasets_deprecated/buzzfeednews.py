#!/usr/bin/env python

from .. import utils
from .. import claimreview

source_name = "buzzfeednews"
location = utils.data_location / source_name


def main():
    source_location = location / "source" / "2018-12-fake-news-top-50" / "data"
    all_domains = (
        utils.read_tsv(source_location / "sites_2016.csv", delimiter=",")
        + utils.read_tsv(source_location / "sites_2017.csv", delimiter=",")
        + utils.read_tsv(source_location / "sites_2018.csv", delimiter=",")
    )

    single_domains = set([el["domain"] for el in all_domains])

    domains = [
        {"domain": el, "label": "fake", "source": source_name} for el in single_domains
    ]

    assessments = []
    source = utils.read_sources()[source_name]["url"]
    for d in domains:
        domain = d["domain"]
        label = d["label"]
        credibility = claimreview.credibility_score_from_label(label)
        assessments.append(
            {
                "from": source,
                "to": domain,
                "link_type": "assesses",
                "credibility": credibility,
                "confidence": 1.0,
                "generated_by": source_name,
                "original_evaluation": label,
            }
        )

    utils.write_json_with_path(assessments, location, "domain_assessments.json")

    utils.write_json_with_path(domains, location, "domains.json")
