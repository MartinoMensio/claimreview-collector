import os
import json
import glob
import shutil
import random
import requests
import datetime
from pathlib import Path
from goose3 import Goose
from urllib.parse import urlparse
from typing import Dict, Optional, List

from . import (
    utils,
    extract_claim_reviews,
    extract_tweet_reviews,
    database_builder,
    cache_manager,
    ukraine_retrieve,
)
from .. import scrapers
from ..publishing import github

# only used in ROLE=full to notify the light instance
MISINFO_BACKEND = os.environ.get("MISINFO_BACKEND", None)
print("MISINFO_BACKEND", MISINFO_BACKEND)
base_path = os.getcwd()
folder = "data"
index_path = f"{folder}/index.json"
latest_data_path = f"{folder}/latest"
PUBLISH_GITHUB = os.environ.get("PUBLISH_GITHUB", False)
CREDIBILITY_BACKEND = os.environ.get("CREDIBILITY_BACKEND", None)
print("CREDIBILITY_BACKEND", CREDIBILITY_BACKEND)

random_misinforming_samples = {
    "misinforming_items": None,
    "length": 0,
    "random_indices": None,
    "ready": False,
}

latest_factchecks = {"items": None, "ready": False}


def load_random_samples():
    meta = get_index_entry()
    file_path = meta["files"]["links_not_credible_full"]
    misinfo_items = utils.read_json(file_path)
    length = len(misinfo_items)
    random_indices = list(range(length))
    random.shuffle(random_indices)
    random_misinforming_samples["misinforming_items"] = misinfo_items
    random_misinforming_samples["length"] = length
    random_misinforming_samples["random_indices"] = random_indices
    random_misinforming_samples["ready"] = True
    print("loaded random samples")


def get_latest_factchecks():
    if not latest_factchecks["ready"]:
        load_latest_factchecks()
    return latest_factchecks["items"]


def load_latest_factchecks():
    meta = get_index_entry()
    file_path = meta["files"]["claim_reviews"]
    claim_reviews = utils.read_json(file_path)
    # TODO define policy e.g. max 2 for each fact-checker
    for el in claim_reviews:
        dates = [r["date_published"] for r in el["reviews"]]
        dates = [el for el in dates if el]
        if dates:
            el["date_published"] = max(dates)
        else:
            el["date_published"] = None
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    filtered_claim_reviews = [
        el
        for el in claim_reviews
        if el["date_published"] and el["date_published"] <= today
    ]
    latest_100 = sorted(
        filtered_claim_reviews, key=lambda el: el["date_published"], reverse=True
    )[:100]
    latest = []
    goose = Goose()
    for el in latest_100:
        try:
            page_text = cache_manager.get(
                el["review_url"],
                unshorten=False,
                verify=False,
                headers={
                    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
                    "Cookie": "wp_gdpr=1|1;",
                },
            )
            article = goose.extract(raw_html=page_text)
            el["goose"] = article.infos
            latest.append(el)
            if len(latest) >= 10:
                break
        except Exception as e:
            print(e)
    # TODO filter by fact-checkers:
    # - double-check what the different fact-checkers show here, e.g. ellinikahoaxes contains title and description of CloudFlare DDoS protection
    # - language filtering: what is the lanugage of our public? Does it make sense to show weird characters?
    latest_factchecks["items"] = latest
    latest_factchecks["ready"] = True
    print("loaded latest factchecks")


def list_data(since: Optional[str] = None, until: Optional[str] = None):
    if os.path.isfile(index_path):
        items = utils.read_json(index_path)
    else:
        items = {}
    if since:
        items = {k: v for k, v in items.items() if k >= since}
    if until:
        items = {k: v for k, v in items.items() if k <= until}
    return items


def get_index_entry(date: str = "latest"):
    data_entries = list_data()
    if date not in data_entries:
        # TODO manage errors
        return "nothing for that date"
    data = data_entries[date]
    return data


def get_data_file_path(file: str, date: str = "latest"):
    index_entry = get_index_entry(date)
    files = index_entry["files"]
    if file not in files:
        # TODO manage errors
        return "no such file, remove this parameter to see the available files"
    # extension = 'zip' if file == 'zip' else 'json'
    # file_name = file if file != 'zip' else date
    file_path = files[file]
    print(file_path)
    if not os.path.isfile(file_path):
        # TODO manage errors
        return "file not found on disk"
    return file_path


def download_data(date: str):
    # download asset
    asset_name = f"{date}.zip"
    asset_path = f"{folder}/{asset_name}"
    bytes_stats = github.get_release_asset_from_tag(date, "stats.json")
    bytes_assets = github.get_release_asset_from_tag(date, asset_name)
    with open(asset_path, "wb") as f:
        f.write(bytes_assets)
    shutil.unpack_archive(asset_path, folder)
    # also overwrite 'latest' folder
    if os.path.isdir(latest_data_path):
        shutil.rmtree(latest_data_path)
    shutil.copytree(f"{folder}/{date}", latest_data_path)

    # update index
    index = list_data()
    stats = json.loads(bytes_stats.decode())
    index[date] = stats
    index["latest"] = stats
    utils.write_json_with_path(index, Path(folder), "index.json")

    # load into DB
    # get_data(date, 'claimreviews')
    with open(stats["files"]["claim_reviews_raw_recollected"]) as f:
        claimreviews_raw = json.load(f)
    database_builder.add_claimreviews_raw(claimreviews_raw)

    # remove old files
    dates_to_remove = index.keys() - ["latest", date]
    for d in dates_to_remove:
        try:
            del index[d]
            shutil.rmtree(f"{folder}/{d}")
        except Exception as e:
            print(e)

    # reload random samples
    load_random_samples()
    # and provide newest factchecks
    load_latest_factchecks()


def check_satisfy(
    el,
    since=None,
    until=None,
    misinforming_domain=None,
    exclude_misinfo_domain=["twitter.com", "wikipedia.org"],
    fact_checker_domain=None,
    exclude_homepage_url_misinfo=True,
):
    dates = [r["date_published"] for r in el["reviews"]]
    fc_domains = [r["fact_checker"]["domain"] for r in el["reviews"]]
    url = el["misinforming_url"]
    # blacklist
    if url in [
        "http://www.aps.sn/actualites/economie/agriculture/",
        "https://www.instagram.com/instablog9ja/",  # whole account, https://dubawa.org/a-blog-claims-man-died-from-suffocation-after-wearing-mask-experts-wade-in/
    ]:
        return False
    if since and not any([d >= since for d in dates if d]):
        return False
    if until and not any([d <= until for d in dates if d]):
        return False
    if not misinforming_domain and exclude_misinfo_domain:
        if el["misinforming_domain"] in exclude_misinfo_domain:
            return False
    if misinforming_domain and misinforming_domain != el["misinforming_domain"]:
        return False
    if fact_checker_domain and not any([d == fact_checker_domain for d in fc_domains]):
        return False
    if exclude_homepage_url_misinfo:
        path = urlparse(url).path
        # non-meaningful path: homepage or facebook.com/permalink.php or any other messed-up things
        if not path or path == "/" or path == "/permalink.php":
            return False
        # if only one path part in these domains, it means it is an account
        if misinforming_domain in ["instagram.com", "facebook.com", "twitter.com"]:
            if len([el for el in path.split("/") if el]) == 1:
                return False
    return True


def random_sample(
    since: Optional[str] = "2019-01-01",
    until: Optional[str] = None,
    misinforming_domain: Optional[str] = None,
    fact_checker_domain: Optional[str] = None,
    exclude_misinfo_domain: Optional[List[str]] = ["twitter.com", "wikipedia.org"],
    exclude_homepage_url_misinfo: Optional[bool] = True,
    cursor: Optional[int] = None,
):
    # first of all make sure that random stuff is loaded
    if not random_misinforming_samples["ready"]:
        load_random_samples()
    # if no cursor, create a random starting point
    if cursor == None:
        # random cursor between 0 (included) and length (excluded)
        cursor = random.randrange(random_misinforming_samples["length"])
    try:
        # align to resume search
        cursor_index = random_misinforming_samples["random_indices"].index(cursor)
    except:
        # if out of range, give a random one
        print("cursor", cursor, "out of range", random_misinforming_samples["length"])
        cursor = random.randrange(random_misinforming_samples["length"])
        cursor_index = random_misinforming_samples["random_indices"].index(cursor)
    # create cursored array by splitting after cursor and merging swapped: indices[cursor:length] + indices[0:cursor1]
    cursored_array = (
        random_misinforming_samples["random_indices"][cursor_index:]
        + random_misinforming_samples["random_indices"][:cursor_index]
    )
    # now start the search with the filters
    match = None
    match_index = None
    current_cursor = cursor
    for cursor in cursored_array:
        el = random_misinforming_samples["misinforming_items"][cursor]
        satisfies = check_satisfy(
            el,
            since,
            until,
            misinforming_domain,
            exclude_misinfo_domain,
            fact_checker_domain,
            exclude_homepage_url_misinfo,
        )
        if not satisfies:
            continue
        if match:
            # for the next round, updating
            break
        else:
            match = el
            match_index = cursor

    if not match:
        return None
    return {
        "sample": match,
        "index": match_index,
        "next_cursor": cursor,
        "current_cursor": current_cursor,
    }


def update_data():
    result_stats = {}
    today = datetime.datetime.today().strftime("%Y_%m_%d")
    print("today", today)
    zip_path = f"{folder}/{today}.zip"
    today_path = f"{folder}/{today}"

    # run scrapers
    stats_scrapers = scrapers.scrape_daily()
    result_stats["scrapers_stats"] = stats_scrapers
    # extract
    cr_stats = extract_claim_reviews.extract_ifcn_claimreviews()
    # tw_stats = extract_tweet_reviews.extract() # TODO this is the slowest, keep the tweets cached in twitter_connector
    result_stats["claim_reviews"] = cr_stats
    # result_stats['tweet_reviews'] = tw_stats

    # copy latest to today folder
    if os.path.isdir(today_path):
        shutil.rmtree(today_path)
    shutil.copytree(latest_data_path, today_path)

    # zip everything
    if os.path.exists(zip_path):
        os.remove(zip_path)

    make_archive(today_path, f"{today_path}.zip")

    files = glob.glob(f"{today_path}/**")
    files = {f.split("/")[-1].replace(".json", ""): f for f in files}
    files["zip"] = zip_path

    result_stats["files"] = files
    result_stats["date"] = today

    # save index
    index = list_data()
    index[today] = result_stats
    index["latest"] = result_stats
    utils.write_json_with_path(index, Path(folder), "index.json")

    # compute ukraine data
    try:
        ukraine_stats = ukraine_retrieve.collect(date=today)
        result_stats["ukraine_stats"] = ukraine_stats
        include_ukraine = True
    except Exception as e:
        print(e)
        include_ukraine = False

    try:
        if PUBLISH_GITHUB:
            github.create_release(
                date=today, result_stats=result_stats, include_ukraine=include_ukraine
            )
            notify_light_instance(result_stats)
    except Exception as e:
        print(e)

    try:
        update_credibility_origins()
    except Exception as e:
        print(e)

    return result_stats


def notify_light_instance(stats):
    """send a POST request to misinfome data update"""
    res = requests.post(f"{MISINFO_BACKEND}/misinfo/api/data/update", json=stats)
    print('notify_light_instance', res.status_code, res.text)
    res.raise_for_status()

def update_credibility_origins():
    """notify light instance to update credibility fact-checkers"""
    if CREDIBILITY_BACKEND:
        res = requests.post(f"{CREDIBILITY_BACKEND}/origins")
        print('update_credibility_origins', res.status_code, res.text)
        res.raise_for_status()

def make_archive(source, destination):
    # http://www.seanbehan.com/how-to-use-python-shutil-make_archive-to-zip-up-a-directory-recursively-including-the-root-folder/
    base = os.path.basename(destination)
    name = base.split(".")[0]
    format = base.split(".")[1]
    archive_from = os.path.dirname(source)
    archive_to = os.path.basename(source.strip(os.sep))
    print(source, destination, archive_from, archive_to)
    shutil.make_archive(name, format, archive_from, archive_to)
    shutil.move("%s.%s" % (name, format), destination)
