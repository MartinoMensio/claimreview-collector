#!/usr/bin/env python

# puts together all the datasets

import os
import json
import glob
import shutil
import signal
import sys
from dateutil import parser
from unidecode import unidecode
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

from . import utils
from . import unshortener
from . import claimreview
from . import database_builder


def normalise_str(string):
    string = unidecode(string)
    string = string.lower()
    string = string.replace('"', "")
    string = string.replace("'", "")
    string = string.replace("  ", " ")
    return string


def select_best_candidate(fcu, matches):
    """Determine whether the fact_checking_url should be matched with any of the candidates, otherwise return None"""
    # the ones that pass the compulsory comparison
    matching_criteria = []
    affinities = []
    for m in matches:
        # the URL has been already compared
        if m["url"] == fcu["url"]:
            matching_criteria.append(m)
            affinities.append(0)
    for idx, m in enumerate(matching_criteria):
        for k, v in fcu.items():
            if k == "source":
                # the source has not to be compared
                continue
            if v and k in m and m[k]:
                prev = m[k]
                cur = v
                if k == "claim":
                    # text normalisation
                    prev = normalise_str(prev)
                    cur = normalise_str(cur)
                if k == "date":
                    prev = parser.parse(prev).date()
                    cur = parser.parse(cur).date()
                if k == "original_label":
                    # ignore this property, too sensitive. There is already the 'label'
                    continue

                if prev != cur:
                    # if some values are different, this is a different claimReview
                    print(k, m["url"], v, m[k])
                    affinities[idx] = -50
                else:
                    affinities[idx] += 1

    best = None
    best_affinity = -1
    for idx, (affinity, m) in enumerate(zip(affinities, matching_criteria)):
        if affinity >= 0:
            if affinity > best_affinity:
                best = m
                best_affinity = affinity

    return best


def merge_fact_checking_urls(aggregated_fact_checking_urls, by_url, fcu):
    matches = by_url[fcu["url"]]
    candidate = select_best_candidate(fcu, matches)
    merged = merge_fact_checking_urls_with_candidates(candidate, fcu)
    # database_builder.load_fact_checking_url(merged)
    if not candidate:
        by_url[fcu["url"]].append(merged)
        aggregated_fact_checking_urls.append(merged)
    return aggregated_fact_checking_urls


def merge_fact_checking_urls_with_candidates(old, new):
    if not old:
        result = {**new}
        result["source"] = [new["source"]]
    else:
        # TODO fields that cannot be merged
        # if new['source'] not in old['source']:
        if "label" in new and "label" in old and new["label"] != old["label"]:
            if new["label"] != None and old["label"] != None:
                if new["claim"] != old["claim"]:
                    raise ValueError("retry")
                    # TODO this will be fixed shortly
                else:
                    print(old)
                    print(new)
                    raise ValueError("abort")
        # result = {**old, **{k:v for k,v in new.items() if v!=None}}
        result = old
        # print(old['source'], new['source'])
        for k, v in new.items():
            if k == "source":
                result["source"] = list(set(old["source"] + [new["source"]]))
            else:
                if v != None and v != "":
                    result[k] = v
    return result


def merge_rebuttals(rebuttals_for_url, new_rebuttal):
    print(rebuttals_for_url, new_rebuttal)
    match = next(
        (el for el in rebuttals_for_url if el["url"] == new_rebuttal["url"]), None
    )
    if not match:
        match = {"url": new_rebuttal["url"], "source": []}
        rebuttals_for_url.append(match)

    match["source"] = list(set(match["source"] + new_rebuttal["source"]))

    return rebuttals_for_url


def merge_fact_checkers(all_fact_checkers, new_fact_checker):
    print(new_fact_checker)
    match = next(
        (el for el in all_fact_checkers if el["domain"] == new_fact_checker["domain"]),
        None,
    )
    if not match:
        match = {}
        all_fact_checkers.append(match)

    for k, v in new_fact_checker.items():
        if k == "source":
            match["sources"] = list(set(match.get("sources", []) + [v]))
        else:
            if k in match and match[k] and v:
                if k == "properties":
                    match[k] = {**match[k], **new_fact_checker[k]}
                else:
                    if v != match[k]:
                        print(
                            "different",
                            k,
                            match[k],
                            new_fact_checker[k],
                            ":for:",
                            new_fact_checker["name"],
                        )
                        if new_fact_checker["source"] != "ifcn":
                            v = match[k]
                        # raise ValueError('ohoho')
            if v != None and v != "":
                match[k] = v


def get_choices():
    # decide here what to aggregate
    choices = {
        k: {
            # TODO rename to url_labels
            "urls": el["contains"].get("url_classification", False),
            # TODO rename to domain_labels
            "domains": el["contains"].get("domain_classification", False),
            # TODO rename to rebuttals
            "rebuttals": el["contains"].get("rebuttal_suggestion", False),
            # TODO rename to claim_reviews
            "claimReviews": el["contains"].get("claimReviews", False),
            "fact_checking_urls": el["contains"].get("fact_checking_urls", False),
            "fact_checkers": el["contains"].get("fact_checkers", False),
        }
        for k, el in utils.read_sources().items()
    }

    return choices


def aggregate_initial():
    all_urls = []
    all_domains = []
    all_domain_assessments = []
    all_rebuttals = defaultdict(list)
    all_claimreviews = []
    aggregated_fact_checking_urls = []
    all_fact_checking_urls_by_url = defaultdict(list)
    all_fact_checkers = []
    # step 1: load types of data natively
    for subfolder, config in get_choices().items():
        if config["urls"] and False:
            urls = utils.read_json(utils.data_location / subfolder / "urls.json")
            all_urls.extend(urls)
        if config["domains"] and False:
            if subfolder != "ifcn":
                # ifcn is broken
                domains = utils.read_json(
                    utils.data_location / subfolder / "domains.json"
                )
            all_domains.extend(domains)
            domain_assessments = utils.read_json(
                utils.data_location / subfolder / "domain_assessments.json"
            )
            all_domain_assessments.extend(domain_assessments)
        if config["rebuttals"] and False:
            rebuttals = utils.read_json(
                utils.data_location / subfolder / "rebuttals.json"
            )
            for source_url, rebuttal_l in rebuttals.items():
                for rebuttal_url, source in rebuttal_l.items():
                    all_rebuttals[source_url] = merge_rebuttals(
                        all_rebuttals.get(source_url, []),
                        {"url": rebuttal_url, "source": source},
                    )
        if config["claimReviews"]:
            claimReview = utils.read_json(
                utils.data_location / subfolder / "claimReviews.json"
            )
            all_claimreviews.extend(claimReview)
        if config["fact_checking_urls"] and False:
            # TODO add these URLs to the collection list, they are needed for retrieving even more claimReviews
            fact_checking_urls = utils.read_json(
                utils.data_location / subfolder / "fact_checking_urls.json"
            )
            for fcu in fact_checking_urls:
                # mongo limits on indexed values
                fcu["url"] = fcu["url"][:1000]
                if fcu.get("claim_url", None):
                    fcu["claim_url"][:1000]

                # matches = database_builder.get_fact_checking_urls(fcu['url'])
                merge_fact_checking_urls(
                    aggregated_fact_checking_urls, all_fact_checking_urls_by_url, fcu
                )

        if config["fact_checkers"] and False:
            fact_checkers = utils.read_json(
                utils.data_location / subfolder / "fact_checkers.json"
            )
            for fc in fact_checkers:
                merge_fact_checkers(all_fact_checkers, fc)

    urls_cnt = len(all_urls)
    domains_cnt = len(all_domains)
    fake_urls_cnt = len([el for el in all_urls if el["label"] == "fake"])
    fake_domains_cnt = len([el for el in all_domains if el["label"] == "fake"])
    print(
        "before aggregation #urls",
        urls_cnt,
        ": fake",
        fake_urls_cnt,
        "true",
        urls_cnt - fake_urls_cnt,
    )
    print(
        "before aggregation #domains",
        domains_cnt,
        ": fake",
        fake_domains_cnt,
        "true",
        domains_cnt - fake_domains_cnt,
    )

    aggregated_urls = utils.aggregate(all_urls)
    aggregated_domains = utils.aggregate(all_domains, "domain")

    utils.write_json_with_path(
        aggregated_urls, utils.data_location, "aggregated_urls.json"
    )
    utils.write_json_with_path(
        aggregated_domains, utils.data_location, "aggregated_domains.json"
    )
    utils.write_json_with_path(
        all_domain_assessments,
        utils.data_location,
        "aggregated_domain_assessments.json",
    )
    utils.write_json_with_path(
        all_rebuttals, utils.data_location, "aggregated_rebuttals.json"
    )
    utils.write_json_with_path(
        all_claimreviews, utils.data_location, "aggregated_claimReviews.json"
    )
    utils.write_json_with_path(
        aggregated_fact_checking_urls,
        utils.data_location,
        "aggregated_fact_checking_urls.json",
    )
    utils.write_json_with_path(
        all_fact_checkers, utils.data_location, "aggregated_fact_checkers.json"
    )

    utils.print_stats(aggregated_urls)
    utils.print_stats(aggregated_domains)
    print("len aggregated fact_checking_urls", len(aggregated_fact_checking_urls))

    # TODO URL unshortening of datasets
    to_be_mapped = [url for url in aggregated_urls.keys()]
    # unshortener.unshorten(to_be_mapped)


def load_into_db():
    # build the database
    # database_builder.clean_db()
    # database_builder.create_indexes()
    # database_builder.load_datasets()
    # database_builder.load_fact_checkers()
    # # # load into database the beginning
    # database_builder.load_urls_zero(file_name='aggregated_urls_with_fcu.json')
    # database_builder.load_domains_zero(file_name='aggregated_domains_with_factchecking_and_stats.json')
    # database_builder.load_domain_assessments()
    # database_builder.load_rebuttals_zero(
    #     file_name='aggregated_rebuttals_with_fcu.json')
    # database_builder.load_fact_checking_urls_zero()

    # database_builder.load_claimReviews()
    raise NotImplementedError()


def check_and_add_url(new_url, new_label, new_sources, aggregated_urls):
    match = aggregated_urls.get("url", None)
    if match:
        print(match, new_url)
        exit(0)
        sources = match["sources"]
        label = match["label"]
        if label != new_label:
            raise ValueError("labels differ: old {} new {}".format(label, new_label))
        sources += new_sources
    else:
        label = new_label
        sources = new_sources
    aggregated_urls[new_url] = {"label": label, "sources": sources}


def extract_more():
    """
    Extracts the additional informations:
    From fact_checking_urls:
    - if el['claim_url'] and el['label']: add url with label
    - if el['url']: add url with 'true' label (the fact checker is trustworthy??)
    From fact_checkers:
    - add domain to the list of domains
    """
    fact_checking_urls = utils.read_json(
        utils.data_location / "aggregated_fact_checking_urls.json"
    )
    classified_urls = utils.read_json(utils.data_location / "aggregated_urls.json")
    classified_domains = utils.read_json(
        utils.data_location / "aggregated_domains.json"
    )
    rebuttals = utils.read_json(utils.data_location / "aggregated_rebuttals.json")
    fact_checkers = utils.read_json(
        utils.data_location / "aggregated_fact_checkers.json"
    )

    print("BEFORE extract_more")
    utils.print_stats(classified_urls)

    for fcu in fact_checking_urls:
        url = fcu.get("url", None)
        claim_url = fcu.get("claim_url", None)
        label = fcu.get("label", None)
        sources = fcu["source"]
        if url and url != "":
            check_and_add_url(url, "true", sources, classified_urls)
        if claim_url and label:
            check_and_add_url(claim_url, label, sources, classified_urls)
            if claim_url not in rebuttals:
                rebuttals[claim_url] = []
            rebuttals[claim_url] = merge_rebuttals(
                rebuttals.get(claim_url, []), {"url": url, "source": sources}
            )

    for fc in fact_checkers:
        domain = fc["domain"]
        match = classified_domains.get(domain, None)
        if not match:
            match = {"sources": []}
            classified_domains[domain] = match
        else:
            if match["label"] != "true":
                raise ValueError(
                    '{} is a fact checker that is not behaving well: "{}"'.format(
                        domain, match["label"]
                    )
                )
        match["label"] = "true"
        match["sources"].extend(fc["sources"])
        match["is_fact_checker"] = True

    print("AFTER extract_more")
    utils.print_stats(classified_urls)

    utils.write_json_with_path(
        classified_urls, utils.data_location, "aggregated_urls_with_fcu.json"
    )
    utils.write_json_with_path(
        rebuttals, utils.data_location, "aggregated_rebuttals_with_fcu.json"
    )
    utils.write_json_with_path(
        classified_domains,
        utils.data_location,
        "aggregated_domains_with_fact_checkers.json",
    )


def retrieve_all_fact_checking_from_source():
    print("now retrieveing original claimReviews from the source")

    starting_fact_checking_urls = utils.read_json(
        utils.data_location / "aggregated_fact_checking_urls.json"
    )

    all_retrieved_claimreviews = []
    result = []

    source_found = 0
    source_not_found = 0
    exceptions = 0

    for i, fcu in enumerate(tqdm(starting_fact_checking_urls)):
        all_fact_checking_urls_by_url = defaultdict(list)
        retrieved_claimreviews = claimreview.get_claimreview_from_factcheckers(
            fcu["url"]
        )
        all_retrieved_claimreviews.extend(retrieved_claimreviews)
        if retrieved_claimreviews:
            source_found += 1
            for cr in retrieved_claimreviews:
                try:
                    new_fact_checking_url = claimreview.to_fact_checking_url(
                        cr, source="from_source"
                    )
                except Exception as e:
                    print(cr)
                    raise e
                merge_fact_checking_urls(
                    result, all_fact_checking_urls_by_url, new_fact_checking_url
                )
        else:
            source_not_found += 1
            merge_fact_checking_urls(result, all_fact_checking_urls_by_url, fcu)
        # if not (i % 100):
        #     print('source_found', source_found, 'source_not_found', source_not_found)

    utils.write_json_with_path(
        result, utils.data_location, "aggregated_fact_checking_urls_source.json"
    )
    # TODO next step should use that


def domain_aggregate_claim_urls():
    """Computes for each domain statistics coming from fact_checking_urls"""
    fact_checking_urls = utils.read_json(
        utils.data_location / "aggregated_fact_checking_urls.json"
    )
    domains = utils.read_json(
        utils.data_location / "aggregated_domains_with_fact_checkers.json"
    )
    for k, v in domains.items():
        v["factchecking_stats"] = defaultdict(set)
    # domains_stats = defaultdict(lambda: defaultdict(set))
    for fcu in fact_checking_urls:
        url = fcu.get("url", None)
        claim_url = fcu.get("claim_url", None)
        label = fcu.get("label", None)
        if claim_url and label:
            for k, v in domains.items():
                domain = utils.get_url_domain(claim_url)
                # domains_stats[domain][label].add(url)
                if k in domain:
                    v["factchecking_stats"][label].add(url)

    for k, v in domains.items():
        # for l, v2 in v['factchecking_stats'].items():
        v["factchecking_stats"] = {
            k2: list(v2) for k2, v2 in v["factchecking_stats"].items()
        }

    # domains_stats = {k: {k2: list(v2) for k2,v2 in v.items()} for k,v in domains_stats.items()}
    utils.write_json_with_path(
        domains,
        utils.data_location,
        "aggregated_domains_with_factchecking_and_stats.json",
    )
    # print(len(domains_stats))


def main():
    aggregate_initial()
    # #retrieve_all_fact_checking_from_source()
    # extract_more()
    # domain_aggregate_claim_urls()
    load_into_db()
