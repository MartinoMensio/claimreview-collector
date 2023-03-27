#!/usr/bin/env python

from .. import utils
from .. import claimreview

location = utils.data_location / "domain_list"


def default_mapping():
    return {
        "domain_col": "domain",
        "label_col": "label",
        "true_vals": ["true"],
        "fake_vals": ["fake"],
    }


def fakenewswatch_mapping():
    default = default_mapping()
    default["fake_vals"] = ["fake_hoax", "clickbait"]
    default["true_vals"] = []
    return default


def usnews_mapping():
    default = default_mapping()
    default["fake_vals"] = ["hoax"]
    return default


def politifact_mapping():
    default = default_mapping()
    default["label_col"] = "Type of site"
    default["fake_vals"] = ["Fake news", "Imposter site"]
    return default


filecolumns = {
    "cbsnews": default_mapping(),
    "dailydot": default_mapping(),
    "fakenewswatch": fakenewswatch_mapping(),
    "newrepublic": default_mapping(),
    "npr": default_mapping(),
    "snopes": default_mapping(),
    "thoughtco": default_mapping(),
    "usnews": usnews_mapping(),
    "politifact": politifact_mapping(),
}


def process_all():
    all_domains = []
    for source in filecolumns.keys():
        partial = process_one_list(source)
        all_domains.extend(partial)

    utils.write_json_with_path(all_domains, location, "domains.json")
    return all_domains


def process_one_list(source):
    # save separately the domains for each list
    mappings = filecolumns[source]
    data = utils.read_tsv(location / "intermediate" / "{}.tsv".format(source))
    print(source)
    source_name = "domain_list_{}".format(source)
    domains = [
        {
            "domain": el[mappings["domain_col"]].lower(),
            "label": "true"
            if el[mappings["label_col"]] in mappings["true_vals"]
            else "fake",
            "source": source_name,
        }
        for el in data
        if el[mappings["label_col"]] in mappings["true_vals"] + mappings["fake_vals"]
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

    utils.write_json_with_path(
        assessments, utils.data_location / source_name, "domain_assessments.json"
    )

    utils.write_json_with_path(
        domains, utils.data_location / source_name, "domains.json"
    )

    return domains


def main(source=None):
    if not source:
        return process_all()
    else:
        return process_one_list(source)
