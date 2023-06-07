import os
import json
import requests
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
from pathlib import Path


from . import database_builder, utils, data_manager
from ..scrapers.implementations import ukrainefacts, euvsdisinfo

from ..main import ROLE

ukraine_path = "data/ukraine"

textrazor_keys = []
if ROLE == "full":
    for textrazor_n_keys in range(1, 100):
        textrazor_key = os.getenv(f"TEXTRAZOR_KEY_{textrazor_n_keys}")
        if textrazor_key is not None:
            textrazor_keys.append(textrazor_key)
        else:
            break
    if len(textrazor_keys) == 0:
        raise ValueError("no textrazor keys found")
    textrazor_key_active = 0


def get_language(text):
    global textrazor_key_active
    lang = database_builder.language_get(text)
    if lang:
        return lang
    else:
        res = requests.post(
            "https://api.textrazor.com/",
            headers={
                "X-TextRazor-Key": textrazor_keys[textrazor_key_active],
            },
            data={
                "text": text,
            },
        )
        textrazor_key_active = (textrazor_key_active + 1) % len(textrazor_keys)
        if res.status_code != 200:
            print(res.text)
            error = res.json()["error"]
            if "TextRazor cannot analyze documents of language: " in error:
                language = error.split(
                    "TextRazor cannot analyze documents of language: "
                )[1][:3]
            else:
                raise ValueError(error)
        else:
            language = res.json()["response"]["language"]
        database_builder.language_put(text, language)
        return language


def clean_sample_ukraine():
    links = utils.read_json("data/latest/links_all_full.json")

    # check satisfy condition
    links = [el for el in links if data_manager.check_satisfy(el)]

    for el in links:
        date = max(
            (r["date_published"] for r in el["reviews"] if r["date_published"]),
            default="0",
        )
        el["date_published"] = date

    # sort by most recent
    sorted_links = sorted(links, key=lambda row: row["date_published"], reverse=True)

    table = [
        {
            "misinforming_url": row["misinforming_url"],
            "misinforming_domain": row["misinforming_domain"],
            "date_published": row["date_published"],
            "n_reviews": len(row["reviews"]),
            "review_url": row["reviews"][0]["review_url"],
            "label": row["reviews"][0]["label"],
            "original_label": row["reviews"][0]["original_label"],
            "fact_checker": row["reviews"][0]["fact_checker"]["name"],
            "country": row["reviews"][0]["fact_checker"]["country"],
            "claim_text": row["reviews"][0]["claim_text"][0].replace("\n", "\\n"),
        }
        for row in sorted_links
    ]

    urls = list(set(el["review_url"] for el in table))

    # ukraine filter
    keyword_list = ["ukraine", "ucraina", "ucrania"]
    with_ukraine = [
        el
        for el in table
        if any(
            keyword in " ".join([el["claim_text"], el["review_url"]]).lower()
            for keyword in keyword_list
        )
    ]

    date_start = "2021-11-01"
    with_ukraine_recent = [
        el for el in with_ukraine if el["date_published"] > date_start
    ]

    for el in tqdm(with_ukraine_recent, desc="getting language"):
        el["factcheck_language"] = get_language(el["claim_text"])

    return with_ukraine_recent


def collect(date: str):
    # data_manager.download_data(date) # already updated
    print("collecting ukraine data: IFCN")
    if not os.path.exists(ukraine_path):
        os.makedirs(ukraine_path)
    ukraine_res = clean_sample_ukraine()
    utils.write_tsv_with_path(
        ukraine_res, Path(f"{ukraine_path}/ukraine_{date}"), "ukraine_IFCN.tsv"
    )
    ifcn_len = len(ukraine_res)

    print("collecting ukraine data: euvsdisinfo")
    # EUVSDISINFO
    euvsdisinfo.main()
    ukraine_res = clean_sample_ukraine()
    utils.write_tsv_with_path(
        ukraine_res, Path(f"{ukraine_path}/ukraine_{date}"), "ukraine_euvsdisinfo.tsv"
    )
    euvsdisinfo_len = len(ukraine_res)

    print("collecting ukraine data: IFCN")
    # ukrainefacts
    ukrainefacts_len = ukrainefacts.main(
        output_path=f"{ukraine_path}/ukraine_{date}/ukraine_ukrainefacts.tsv"
    )

    print("collecting ukraine data: zip")
    # now zip
    folder_path = f"{ukraine_path}/ukraine_{date}"
    zip_path = f"{folder_path}.zip"

    # zip everything
    if os.path.exists(zip_path):
        os.remove(zip_path)

    data_manager.make_archive(folder_path, zip_path)

    return {
        "ifcn_cnt": ifcn_len,
        "euvsdisinfo_cnt": euvsdisinfo_len,
        "ukrainefacts_cnt": ukrainefacts_len,
    }
