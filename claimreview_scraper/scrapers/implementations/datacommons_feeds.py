#!/usr/bin/env python
import requests
import re
from xml.etree import ElementTree

from . import ScraperBase
from ...processing import utils
from ...processing import claimreview
from ...processing import database_builder

feed_directory = 'https://storage.googleapis.com/datacommons-feeds/'
latest_feed = 'claimreview/latest/data.json'

class Scraper(ScraperBase):
    
    def __init__(self):
        self.id = 'datacommons_feeds'
        self.homepage = 'https://www.datacommons.org/factcheck/download#fcmt-data'
        self.name = 'DataCommons - Fact Check Markup Tool Data Feed'
        self.description = 'This is a data feed of ClaimReview markups created via the Google Fact Check Markup Tool and the new ClaimReview Read/Write API. The data in the feed also follows the schema.org ClaimReview standard, namely the same schema as the data in the historical research dataset. The feed itself is in DataFeed format.'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        feed_data = download_latest_feed()
        data_list = feed_data['dataFeedElement']
        database_builder.save_original_data(self.id, data_list)
        claim_reviews = extract_claimreviews(data_list)
        database_builder.add_ClaimReviews(self.id, claim_reviews)
        return claim_reviews


def download_feed(feed_url):
    pieces = feed_url.split('/')
    if len(pieces) != 3:
        return
    version = pieces[1]
    response = requests.get(feed_directory + feed_url)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    data = response.json()
    return data

def extract_claimreviews(data_list):
    claim_reviews = []

    for item in data_list:
        if not item['item']:
            break
        for cr in item['item']:
            if cr:
                # some have "item": null
                claim_reviews.append(cr)

    return claim_reviews

def get_credibility_measures(claim_review):
    rating = claimreview.get_claim_rating(claim_review)
    if rating is None:
        credibility = 0.0
        confidence = 0.0
    else:
        print(rating, claim_review['reviewRating'])
        credibility = (rating - 0.5) * 2
        confidence = 1.0
    return {'credibility': credibility, 'confidence': confidence}


def download_all_feeds():
    response = requests.get(feed_directory)
    if response.status_code != 200:
        raise ValueError(response.status_code)
    response_content = response.text
    # remove the namespace, also if single quoted https://stackoverflow.com/questions/34009992/python-elementtree-default-namespace
    response_content = re.sub(r"""\s(xmlns="[^"]+"|xmlns='[^']+')""", '', response_content, count=1)
    #print(response_content)
    root = ElementTree.fromstring(response_content)
    #print(root)
    for el in root.findall('Contents'):
        #print(el)
        key = el.find('Key').text
        print(key)
        download_feed(key)

def download_latest_feed():
    return download_feed(latest_feed)

def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()