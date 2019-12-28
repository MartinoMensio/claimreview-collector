import requests
from bs4 import BeautifulSoup
import tqdm
from multiprocessing.pool import ThreadPool

from ...processing import claimreview, utils, database_builder
from ... import logger
from .. import ScraperBase

HOMEPAGE = 'https://teyit.org'


class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'teyit_org'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            all_reviews = get_all_articles_url(self.id)
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = [el for el in all_reviews]
        claim_reviews = []
        with ThreadPool(8) as pool:
            urls = [r['url'] for r in all_reviews]
            for one_result in tqdm.tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls), total=len(urls)):
                url_fixed, cr = one_result
                if not cr:
                    print('no claimReview from', url_fixed)
                else:
                    claim_reviews.extend(cr)
        # for r in tqdm(all_reviews):
        #     url_fixed, cr = claimreview.retrieve_claimreview(r['url'])
        #     claim_reviews.extend(cr)
        database_builder.add_ClaimReviews(self.id, claim_reviews)


def collect_article_urls(list_page_url):
    page_no = 1

    page_url = f'{list_page_url}page/{page_no}'
    response = requests.get(page_url)

    urls = []

    while response.status_code != 404:
        soup = BeautifulSoup(response.content,'lxml')
        for article in soup.findAll('article'):
            # TODO check that we have one element with selection 'div a'
            article_url = article.select('div a')[0]['href']
            urls.append(article_url)
            #print(cl_review)
        page_no = page_no + 1
        page_url = f'{list_page_url}page/{page_no}'
        response = requests.get(page_url)
    return urls

def test():
    url = "https://teyit.org/a-haberin-chpnin-akil-almaz-nanoteknolojik-hilesi-alt-bandi-kullandigi-iddiasi/"
    # print(claimreview.get_claimreview_from_factcheckers(url))


def get_all_articles_url(self_id):
    response = requests.get(HOMEPAGE)
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')
    categories = soup.select('div.sayac_widget a')

    all_urls = []
    for c in categories:
        category_list_url = c['href']
        print(category_list_url)
        category_urls = collect_article_urls(category_list_url)
        print(len(category_urls), 'found at', category_list_url)
        all_urls.extend(category_urls)
    
    all_statements = [{'url': el} for el in all_urls]

    database_builder.save_original_data(self_id, all_statements)
    return all_statements

# def get_claim_reviews(all_urls):
#     """DEPRECATED"""
#     all_claim_reviews = []
#     for u in tqdm.tqdm(all_urls):
#         claim_reviews = claimreview.get_claimreview_from_factcheckers(u)
#         if not isinstance(claim_reviews, list):
#             print('not a list at', u, claim_reviews)
#             continue
#         if not claim_reviews:
#             print('no claimReview for', u)
#             # TODO understand why not able to fix the json of:
#             # - https://teyit.org/a-haberin-abdyi-tl-korkusu-sardi-seklinde-bir-alt-bant-kullandigi-iddiasi/
#             # - https://teyit.org/alman-bira-firmasinin-piyasaya-surdugu-bira-sisesinde-la-ilahe-illallah-yazdigi-iddiasi/
#             # - https://teyit.org/diyanet-cocuklara-zeka-gelistirici-oyuncaklar-vermeyin-aciklamasinda-bulundu-mu/
#             # - https://teyit.org/ozdilin-mustafa-kemal-kitabinda-yer-aldigi-iddia-edilen-kuru-fasulye-ve-leblebi-bolumleri/
#             # - https://teyit.org/videonun-fransadaki-sari-yelekliler-eylemleri-sirasinda-macronun-kafasina-yumurta-atildigini-gosterdigi-iddiasi/
#             # - https://teyit.org/odtu-mezuniyetindeki-vajina-yanginina-care-ariyoruz-bulamadik-yazili-pankart-iddiasi/
#             # - https://teyit.org/a-haber-in-muharrem-incenin-izmir-mitingine-katilim-olmadi-alt-bandi-kullandigi-iddiasi/
#             # - https://teyit.org/pankartta-kahrolsun-seriat-basortusune-gecit-yok-yasasin-laiklik-yazdigi-iddiasi/
#             # - https://teyit.org/a-haberin-muharrem-ince-icin-universiteyi-8-donemde-bitirmis-alt-bandi-kullandigi-iddiasi/
#             # - https://teyit.org/adalet-partisi-genel-baskani-vecdet-ozun-tayyip-size-mustahak-dedigi-iddiasi/
#             continue
#         all_claim_reviews.extend(claim_reviews)

#     database_builder.add

def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()
