import io
import csv
import tqdm
import time
import tqdm
import requests
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool

from . import ScraperBase
from ...processing import utils
from ...processing import claimreview
from ...processing import database_builder
from ...processing import unshortener

# https://www.poynter.org/coronavirusfactsalliance/ exposes csv file
# wget https://pudding.cool/misc/covid-fact-checker/data.csv

# TODO See the official file given us here https://drive.google.com/drive/folders/1LzPMpAvpcIQMWgnReXtP15MfiSIYeWjb

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36"
}


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "poynter_covid"
        self.homepage = "https://www.poynter.org/ifcn-covid-19-misinformation"
        self.name = "The CoronaVirusFacts/DatosCoronaVirus Alliance Database"
        self.description = "Full Fact is a registered charity. They actively seek a diverse range of funding and are transparent about all our sources of income."
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = scrape_all(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = list(all_reviews)
        claim_reviews = []
        for r in tqdm.tqdm(all_reviews):
            url = r["URL to fact-checked article (in your language)"]
            try:
                url = unshortener.unshorten(url)
                built_cr = create_claimreview(r, url)
                claim_reviews.append(built_cr)
                url_fixed, cr = claimreview.retrieve_claimreview(url)
                claim_reviews.extend(cr)
            except Exception as e:
                print(e)
                print(url)
                pass
        database_builder.add_ClaimReviews(self.id, claim_reviews)


def scrape_all(self_id):
    results = []
    # res = requests.get('https://pudding.cool/misc/covid-fact-checker/data.json')
    res = requests.get("https://pudding.cool/misc/covid-fact-checker/data.csv")
    # json 2514
    # csv 8325
    res.raise_for_status()
    data = res.text
    reader = csv.DictReader(io.StringIO(data))
    field_names = reader.fieldnames
    print(field_names)
    results = list(reader)

    # page_n = 1

    # # already = database_builder.get_original_data(self_id)
    # # already_by_url = {el['poynter_url']: el for el in already}

    # max_same = 10

    # currently_same = 0
    # while True:
    #     if currently_same > max_same:
    #         break
    #     # url = f'https://www.poynter.org/ifcn-covid-19-misinformation/page/{page_n}/?orderby=views&order=DESC#038;order=DESC'
    #     url = f'https://www.poynter.org/ifcn-covid-19-misinformation/page/{page_n}/?orderby=views&order=ASC#038;order=ASC'

    #     response = requests.get(url, headers=headers)
    #     response.raise_for_status()
    #     soup = BeautifulSoup(response.text, 'lxml')

    #     rows = soup.select('article')
    #     print(f'Found {len(rows)} articles at page {page_n}')
    #     if not len(rows):
    #         break

    #     with ThreadPool(8) as pool:

    #         for el in tqdm.tqdm(pool.imap(extract_row, rows), total=len(rows)):
    #             # if el['poynter_url'] in already_by_url:
    #             #     print('same', currently_same)
    #             #     currently_same += 1
    #             # else:
    #             #     currently_same = 0
    #             #     already_by_url[el['poynter_url']] = el
    #             results.append(el)

    #     page_n += 1

    # # results = list(already_by_url.values())

    with open("poynter_covid.tsv", "w") as f:
        writer = csv.DictWriter(f, field_names, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    database_builder.save_original_data(self_id, results)

    return results


def create_claimreview(row, unshortened_url):
    # - When did you see the claim?                         datePublished
    # - Countries
    # - Organization                                        author.name
    # - What did you fact-check?                            claimReviewed
    # - Who said/posted it?                                 itemReviewed.author
    # - Link to the original piece                          itemReviewed.appearance
    # - URL to fact-checked article (in your language)      url
    # - Language of your fact-check
    # - Final rating                                        reviewRating.alternateName
    # - Explanation                                         reviewRating.explanation
    # - Category
    appearance = row["Link to the original piece"]
    url = unshortened_url
    if appearance:
        # TODO split by space? remove "not available" "Taken down" ...
        # TODO work with wayback machine urls and perma.cc to get the original URL
        try:
            appearances = appearance.split()
            appearances = [el.strip() for el in appearances]
            appearances = [el for el in appearances if el.startswith("http")]
            appearances = [unshortener.unshorten(el) for el in appearances]
            # print(appearances)
        except Exception as e:
            print(appearance)
            appearances = []

    else:
        appearances = []

    claim_review = {
        "@context": "http://schema.org",
        "@type": "ClaimReview",
        "url": url,
        "author": {"@type": "Organization", "name": row["Organization"]},
        "claimReviewed": row["What did you fact-check?"],
        "reviewRating": {
            "@type": "Rating",
            "explanation": row["Explanation"],
            "alternateName": row["Final rating"],
        },
        "itemReviewed": {
            "@type": "Claim",
            "author": {"@type": "Person", "name": row["Who said/posted it?"]},
            "appearance": [{"@type": "CreativeWork", "url": u} for u in appearances],
        },
        "datePublished": row["When did you see the claim?"],
        "origin": "poynter_covid",
    }
    return claim_review


def extract_row(r, retries=5):
    checked_by = (
        r.select_one("header.entry-header p.entry-content__text")
        .text.strip()
        .replace("Fact-Checked by: ", "")
    )
    date, location = [
        el.strip()
        for el in r.select_one(
            "header.entry-header p.entry-content__text strong"
        ).text.split("|")
    ]

    title_el = r.select_one("h2.entry-title a")
    label_and_title = title_el.text.strip()
    label = label_and_title.split(":")[0]
    title = label_and_title.replace(label, "")[2:].strip()
    poynter_url = title_el["href"]

    el = {
        "checked_by": checked_by,
        "date": date,
        "location": location,
        "label": label,
        "title": title,
        "poynter_url": poynter_url,
    }

    try:
        # Explanation, fact-checker_url and origin are on the detail page
        response = requests.get(poynter_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        if retries:
            # try again
            print(f"Going to retry for {poynter_url}...")
            time.sleep(2)
            return extract_row(r, retries=retries - 1)
        raise e
    # print(response.text)
    soup = BeautifulSoup(response.text, "lxml")

    explanation = (
        soup.select_one("p.entry-content__text--explanation")
        .text.replace("Explanation: ", "")
        .strip()
        .replace("\n", "")
    )
    originated_from = (
        soup.select_one("p.entry-content__text--smaller").text.split(":")[-1].strip()
    )
    factchecker_url = soup.select_one("a.entry-content__button--smaller")["href"]

    # dirty data https://www.poynter.org/?ifcn_misinformation=the-article-includes-a-compilation-of-different-false-claims-and-manipulative-photos-1-false-claim-saying-that-there-was-identified-infected-person-in-georgia-2-false-claim-about-banana-being-a-so
    factchecker_url.replace("In Georgian - ", "")

    el["explanation"] = explanation
    el["originated_from"] = originated_from
    el["factchecker_url"] = factchecker_url
    return el


def main():
    scraper = Scraper()
    scraper.scrape()


if __name__ == "__main__":
    main()
