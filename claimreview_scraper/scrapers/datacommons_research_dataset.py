#!/usr/bin/env python

import extruct
import json
import itertools
import os
import tqdm
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import io
import gzip
from multiprocessing.pool import ThreadPool


from ..processing import utils, unshortener
from ..processing import claimreview, database_builder
from . import Scraper

class DatacommonsResearchScraper(Scraper):
    
    def __init__(self):
        self.id = 'datacommons_research_dataset'
        Scraper.__init__(self)

    def scrape(self):
        original_contents = download_latest_release()
        claim_reviews = load_jsonld(original_contents)
        database_builder.save_original_data(self.id, claim_reviews)
        enriched_claim_reviews = enrich_claimReviews(claim_reviews)
        database_builder.add_ClaimReviews(self.id, enriched_claim_reviews)
        return claim_reviews

def download_latest_release():
    # find the latest release
    homepage = 'https://www.datacommons.org'
    response = requests.get(f'{homepage}/factcheck/download')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')

    download_a = soup.select_one('a#download')
    link = f"{homepage}{download_a['href']}"
    file_name = link.split('/')[-1]
    version = file_name.split('.')[0]
    print('version:', version)

    # download it
    response = requests.get(link)
    compressed_file = io.BytesIO(response.content)
    decompressed_file = gzip.GzipFile(fileobj=compressed_file)
    contents = decompressed_file.read()
    contents = contents.decode('utf-8')
    print(contents[:100])

    return contents

    

def load_jsonld(content):

    # extract the embedded metadata https://github.com/scrapinghub/extruct
    data = extruct.extract(content)

    claimReviews = data['json-ld']

    # some analysis of the labels to see how they are annotated
    labels = set([el['reviewRating']['alternateName'] for el in claimReviews])
    lambda_source = lambda el: el['author']['name']

    # group the labels by the author of the review, to see how each one of them uses the alternateName
    labels_by_sources = {k:set([el['reviewRating']['alternateName'] for el in v]) for k, v in itertools.groupby(sorted(claimReviews, key=lambda_source), key=lambda_source)}

    print('#claimReviews', len(claimReviews))
    print('#labels', len(labels))
    #print('labels', labels)
    print('#different labels for each source', {k:len(v) for k,v in labels_by_sources.items()})

    # save the original claimReviews
    # utils.write_json_with_path(claimReviews, intermediate_path, 'datacommons_claimReviews.json')

    return claimReviews




def enrich_claimReviews(claim_reviews):

    # retrieve the claimReviews with more properties
    # claimReviews_full = get_claimreviews_from_factcheckers(claimReviews)
    result = list(claim_reviews)
    print('before enriching', len(result))
    with ThreadPool(8) as pool:
        print('unshortening')
        urls = []
        for r in tqdm.tqdm(result):
            url = r['url']
            unshorten = False
            if 'bit.ly' in url:
                unshorten = True
            urls.append(claimreview.get_corrected_url(url, unshorten=unshorten))
        print('retrieving')
        for one_result in tqdm.tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls), total=len(urls)):
            url_fixed, cr = one_result
            if not cr:
                # print('no claimReview from', url_fixed)
                pass
            else:
                result.extend(cr)

    print('after enriching', len(result))
    return result


def main():
    scraper = DatacommonsResearchScraper()
    scraper.scrape()


if __name__ == "__main__":
    main()