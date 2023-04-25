"""
This script provides the 4500 tweet reviews dataset
"""

import os
import re
import tqdm
import json
import tldextract
import requests
from collections import defaultdict
from pathlib import Path

from . import unshortener, claimreview

from . import utils, database_builder

TWITTER_CONNECTOR = os.environ.get("TWITTER_CONNECTOR", "http://localhost:20200")
print("TWITTER_CONNECTOR", TWITTER_CONNECTOR)
MISINFO_BACKEND = os.environ.get("MISINFO_BACKEND", "http://localhost:5000")
print("MISINFO_BACKEND", MISINFO_BACKEND)

client = database_builder.client
data_path = Path("data/latest")


### UTILITIES


def get_ifcn_domains():
    """get the list of domains of fact-checkers belonging to IFCN"""
    res = requests.get(f"{MISINFO_BACKEND}/misinfo/api/credibility/factcheckers")
    res.raise_for_status()
    signatories = res.json()

    utils.write_json_with_path(signatories, data_path, "ifcn_sources.json")
    ass = {el["domain"]: el for el in signatories}
    # print(ass)
    print("there are", len(ass), "ifcn trusted domains")
    return ass


### MAPPING FUNCTIONS


def extract():
    """Filtering function that analyses ClaimReviews and extracts tweet ratings."""

    ifcn_domains = get_ifcn_domains()

    filtered_cr = []
    tweet_reviews = defaultdict(
        list
    )  # id: {label (mapped), original_label, id, fulltext}
    not_ifcn_cnt = 0
    not_ifcn_review_domains = set()
    not_twitter_cnt = 0
    errror_tweet_id_cnt = 0
    errror_twitter_api_cnt = 0
    multiple_reviews_cnt = 0
    disagreeing_cnt = 0
    disagreeing_reviews = {}
    for cr in client["claimreview_collector"]["claim_reviews"].find():
        try:
            url = cr.get("url", "")
            domain = utils.get_url_domain(url)
            appearances = claimreview.get_claim_appearances(cr)
            if domain not in ifcn_domains:
                not_ifcn_cnt += 1
                not_ifcn_review_domains.add(domain)
                # raise ValueError(3)
                continue
            twitter_match = False
            review_rating = cr.get("reviewRating", {})
            original_label = review_rating.get("alternateName", "")
            mapped_label = claimreview.get_coinform_label(cr)
            for a in appearances:
                try:
                    match = re.search(
                        r"https://twitter\.com/[A-Za-z0-9_]+/status/(?P<tweet_id>[0-9]+).*",
                        a,
                    )
                    tweet_id = match.group("tweet_id")
                    tweet_id = int(tweet_id)
                # a_domain = utils.get_url_domain(a)
                # if a_domain == 'twitter.com':
                #     try:
                #         if a.endswith('/'):
                #             a = a[:-1]
                #         tweet_id = int(a.split('/')[-1].split('?')[0])
                except Exception:
                    print("not with a tweet id", a)
                    errror_tweet_id_cnt += 1
                    continue

                filtered_cr.append(cr)
                tweet_reviews[tweet_id].append(
                    {
                        "label": mapped_label,
                        "original_label": original_label,
                        "review_rating": review_rating,
                        "claim_reviewed": cr["claimReviewed"],
                        "review_url": cr["url"],
                        "retrieved_by": cr["retrieved_by"],
                    }
                )
                twitter_match = True
            if not twitter_match:
                not_twitter_cnt += 1
        except Exception as e:
            print(e)
            raise ValueError(cr)

    utils.write_json_with_path(
        list(not_ifcn_review_domains), data_path, "not_ifcn_sources.json"
    )

    results = []
    for tweet_id, reviews in tqdm.tqdm(tweet_reviews.items(), desc="second loop"):
        if len(reviews) > 1:
            multiple_reviews_cnt += 1

        # check that the ratings agree
        labels = set(el["label"] for el in reviews)
        if len(labels) > 1:
            disagreeing_cnt += 1
            label = "check_me"
            disagreeing_reviews[tweet_id] = reviews
        else:
            label = labels.pop()

        try:
            res = requests.get(f"{TWITTER_CONNECTOR}/tweets/{tweet_id}")
            res.raise_for_status()
            t = res.json()
            text = t["text"]
            created_at = t["created_at"]
            lang = t["lang"]
            screen_name = t["user_screen_name"]
        except Exception as e:
            print("API error", e, tweet_id)
            errror_twitter_api_cnt += 1
            text = None
            created_at = None
            lang = None
            screen_name = None

        results.append(
            {
                "id": tweet_id,
                "label": label,
                "full_text": text,
                "created_at": created_at,
                "screen_name": screen_name,
                "lang": lang,
                "reviews": reviews,
            }
        )

    utils.write_json_with_path(
        disagreeing_reviews, data_path, "tweet_disagreeing_reviews.json"
    )

    print("not ifcn", not_ifcn_cnt)
    print("not twitter", not_twitter_cnt)
    print("error tweet id", errror_tweet_id_cnt)
    print("error twitter API", errror_twitter_api_cnt)
    print("multiple reviews", multiple_reviews_cnt)
    print("multiple reviews disagreeing", disagreeing_cnt)

    print("there are", len(results), "tweet reviews")

    utils.write_json_with_path(tweet_reviews, data_path, "tweet_reviews.json")
    analyse_mapping()

    return {
        "tweet_reviews_count": len(results),
        "not_twitter_count": not_twitter_cnt,
        "error_tweet_id_count": errror_tweet_id_cnt,
        "error_twitter_api_count": errror_twitter_api_cnt,
        "tweets_with_multiple_reviews_count": multiple_reviews_cnt,
        "tweets_with_disagreeing_reviews_count": disagreeing_cnt,
    }


def analyse_mapping():
    """see what got mapped to what"""
    reviews = utils.read_json(data_path / "tweet_reviews.json")
    m = defaultdict(set)
    for t_id, r in reviews.items():
        for el in r:
            m[el["label"]].add(el["original_label"])
    for k, v in m.items():
        m[k] = list(v)
    utils.write_json_with_path(m, data_path, "tweet_labels_mapping.json")


def filter_data():
    import pandas as pd
    import dateparser

    data = read_json(data_path / "tweet_reviews.json")
    start_date = dateparser.parse("1 september 2020")

    for d in data:
        del d["reviews"]

    df = pd.DataFrame(data)
    parsing_fn = lambda v: dateparser.parse(v.replace("+0000", "")) if v else None
    tweet_url_fn = (
        lambda v: f'https://twitter.com/{v["screen_name"]}/status/{v["id"]}'
        if v["screen_name"]
        else None
    )
    df["created_at_parsed"] = df["created_at"].apply(parsing_fn)
    df["tweet_url"] = df.apply(tweet_url_fn, axis=1)

    df_recent = df[df["created_at_parsed"] >= start_date]
    by_label = df_recent.groupby("label").count()
    df_recent_credible = df_recent[df_recent["label"] == "credible"]
    df_recent_mostly_credible = df_recent[df_recent["label"] == "mostly_credible"]
    df_recent_ok = pd.concat([df_recent_credible, df_recent_mostly_credible])
    df_recent_ok.to_csv(
        "data/tweet_reviews_credible_or_mostly_september_october.tsv",
        sep="\t",
        index=False,
    )

    df_credible = df[df["label"] == "credible"]
    df_mostly_credible = df[df["label"] == "mostly_credible"]
    df_ok = pd.concat([df_credible, df_credible])
    df_ok.to_csv("data/tweet_reviews_credible_or_mostly.tsv", sep="\t", index=False)
    df_ok_en = df_ok[df_ok["lang"] == "en"]
    df_ok_en.to_csv(
        "data/tweet_reviews_credible_or_mostly_english.tsv", sep="\t", index=False
    )


if __name__ == "__main__":
    extract()
