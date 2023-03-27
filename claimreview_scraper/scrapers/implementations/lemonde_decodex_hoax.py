import os
import time
import requests
import itertools
import tqdm

from . import ScraperBase
from ...processing import utils, claimreview, database_builder


class Scraper(ScraperBase):
    def __init__(self):
        self.id = "lemonde_decodex_hoax"
        self.homepage = "https://www.lemonde.fr/verification/"
        self.name = "Le Monde - Les Decodeurs"
        self.description = "The Decodex is a tool to help you check the information circulating on the Internet and find rumors, exaggerations or distortions."
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


hoaxes_location = "https://s1.lemde.fr/mmpub/data/decodex/hoax/hoax_debunks.json"


def get_rating_value(label):
    label = label.lower()
    return {
        "faux": 0,  # false
        "douteux": 0,  # doubt
        "trompeur": 0,  # misleading
        "détourné": 0,
        "infondé": 0,  # without support
        "contestable": 1,  # contestable
        "partiellement faux": 1,  # partially false
        "c’est plus compliqué": 1,  # more complicated
        "c’est plus complique": 1,  # more complicated
        "exagéré": 1,
        "très exagéré": 1,  # very exxagerated
        "a nuancer": 1,  # with caution,
        "prudence": 1,
        "c’est possible": 1,  # it's possible
        "imprécis": 1,  # imprecise
        "vrai": 2,  # true
    }[label]


def create_claimreview_from_hoaxes(hoaxes):
    def by_id_fn(el):
        return el[1]

    appearances_by_debunk_id = itertools.groupby(
        sorted(hoaxes["hoaxes"].items(), key=by_id_fn), key=by_id_fn
    )
    appearances_by_debunk_id = {
        k: list([el[0] for el in v]) for k, v in appearances_by_debunk_id
    }

    claim_reviews = []

    for debunk_id, debunk in hoaxes["debunks"].items():
        title, label, motivation, debunk_url = debunk
        appearances = appearances_by_debunk_id.get(debunk_id, [])
        ratingValue = get_rating_value(label)
        claim_review = {
            "@context": "http://schema.org",
            "@type": "ClaimReview",
            "url": debunk_url,
            "author": {
                "@type": "Organization",
                "name": "Le Monde",
                "url": "https://www.lemonde.fr",
                "logo": "https://asset.lemde.fr/medias/img/social-network/default.png",
                "sameAs": [
                    "https://www.facebook.com/lemonde.fr",
                    "https://twitter.com/lemondefr",
                    "https://www.instagram.com/lemondefr/",
                    "https://www.youtube.com/user/LeMonde",
                    "https://www.linkedin.com/company/le-monde/",
                ],
            },
            "claimReviewed": "",
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": ratingValue,
                "bestRating": 2,
                "worstRating": 0,
                "alternateName": label,
            },
            "itemReviewed": {
                "@type": "Claim",
                "appearance": [
                    {"@type": "CreativeWork", "url": u} for u in appearances
                ],
            },
            "origin": "lemonde_decodex_hoax",
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
