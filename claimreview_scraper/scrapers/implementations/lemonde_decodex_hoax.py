import os
import time
import requests
import itertools

from ...processing import utils, claimreview, database_builder
from .. import ScraperBase
import tqdm

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'lemonde_decodex_hoax'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            hoaxes = download_hoaxes()
            # TODO change serialisation, keys cannot contain dots etc...
            # database_builder.save_original_data(self.id, [hoaxes])
        else:
            hoaxes = database_builder.get_original_data(self.id)[0]
        claim_reviews = create_claimreview_from_hoaxes(hoaxes)
        database_builder.add_ClaimReviews(self.id, claim_reviews)

hoaxes_location = 'https://s1.lemde.fr/mmpub/data/decodex/hoax/hoax_debunks.json'

def get_rating_value(label):
    return {
        'FAUX': 1,
        'DOUTEUX': 2,
        'CONTESTABLE': 3,
        'TROMPEUR': 3 # misleading
    }[label]


def create_claimreview_from_hoaxes(hoaxes):
    def by_id_fn(el): return el[1]
    appearances_by_debunk_id = itertools.groupby(
        sorted(hoaxes['hoaxes'].items(), key=by_id_fn), key=by_id_fn)
    appearances_by_debunk_id = {k: list([el[0] for el in v]) for k, v in appearances_by_debunk_id}

    claim_reviews = []

    for debunk_id, debunk in hoaxes['debunks'].items():
        title, label, motivation, debunk_url = debunk
        appearances = appearances_by_debunk_id.get(debunk_id, [])
        ratingValue = get_rating_value(label)
        claim_review = {
            "@context": "http://schema.org",
            "@type": "ClaimReview",
            "url": debunk_url,
            "author": {
                "@type": "Organization",
                "name":"Le Monde",
                "url":"https://www.lemonde.fr",
                "logo":"https://asset.lemde.fr/medias/img/social-network/default.png",
                "sameAs": ["https://www.facebook.com/lemonde.fr","https://twitter.com/lemondefr","https://www.instagram.com/lemondefr/","https://www.youtube.com/user/LeMonde","https://www.linkedin.com/company/le-monde/"]
            },
            "claimReviewed": "",
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": ratingValue,
                "bestRating": 5,
                "worstRating": 1,
                "alternateName": label
            },
            "itemReviewed": {
                "@type": "Claim",
                "appearance": [{'@type': 'CreativeWork', 'url': u} for u in appearances]
            },
            'origin': 'lemonde_decodex_hoax'
        }

        claim_reviews.append(claim_review)

    return claim_reviews


def download_hoaxes():
    response = requests.get(hoaxes_location)
    if response.status_code != 200:
        print(response.text)
        raise ValueError(response.status_code)

    result = response.json()
    return result



def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()