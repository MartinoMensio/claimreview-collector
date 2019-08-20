import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..processing import claimreview, utils
from .. import logger

HOMEPAGE = 'https://teyit.org'
my_path = utils.data_location / 'teyit_org'


def update_page_url(claim_label, page_no):
    result = f"https://teyit.org/konu/analiz/{claim_label}/page/{page_no}"
    print(result)
    return result


def collect_article_urls(claim_label):
    page_no = 1

    page_url = update_page_url(claim_label, page_no)
    response = requests.get(page_url)

    urls = []

    while response.status_code != 404:
        soup = BeautifulSoup(response.content,'lxml')
        for article in soup.findAll('article'):
            if not article.select('div a'):
                logger.APP_LOGGER.info(f'{cl_review.count()} of {claim_label} claim is extracted.')
                break
            article_url = article.select('div a')[0]['href']
            urls.append(article_url)
            #print(cl_review)
        page_no = page_no + 1
        page_url = update_page_url(claim_label, page_no)
        response = requests.get(page_url)
    return urls

def test():
    url = "https://teyit.org/a-haberin-chpnin-akil-almaz-nanoteknolojik-hilesi-alt-bandi-kullandigi-iddiasi/"
    print(claimreview.retrieve_claimreview(url))


def get_all_articles_url():
    response = requests.get(HOMEPAGE)
    if response.status_code != 200:
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')
    categories = soup.select('div.sayac_widget div.single-sayac div')

    all_urls = []
    for c in categories:
        category_label = c['class'][0]
        print(category_label)
        category_urls = collect_article_urls(category_label)
        all_urls.extend(category_urls)

    utils.write_json_with_path(all_urls, my_path / 'source', 'urls.json')
    return all_urls

def get_claim_reviews(all_urls):
    claim_reviews = []
    for u in tqdm(all_urls):
        claim_review = claimreview.retrieve_claimreview(u)[1]
        if not isinstance(claim_review, list):
            print('not a list at', u, claim_review)
            continue
        if not claim_review:
            print('no claimReview for', u)
            # TODO understand why not able to fix the json of:
            # - https://teyit.org/a-haberin-abdyi-tl-korkusu-sardi-seklinde-bir-alt-bant-kullandigi-iddiasi/
            # - https://teyit.org/alman-bira-firmasinin-piyasaya-surdugu-bira-sisesinde-la-ilahe-illallah-yazdigi-iddiasi/
            # - https://teyit.org/diyanet-cocuklara-zeka-gelistirici-oyuncaklar-vermeyin-aciklamasinda-bulundu-mu/
            # - https://teyit.org/ozdilin-mustafa-kemal-kitabinda-yer-aldigi-iddia-edilen-kuru-fasulye-ve-leblebi-bolumleri/
            # - https://teyit.org/videonun-fransadaki-sari-yelekliler-eylemleri-sirasinda-macronun-kafasina-yumurta-atildigini-gosterdigi-iddiasi/
            # - https://teyit.org/odtu-mezuniyetindeki-vajina-yanginina-care-ariyoruz-bulamadik-yazili-pankart-iddiasi/
            # - https://teyit.org/a-haber-in-muharrem-incenin-izmir-mitingine-katilim-olmadi-alt-bandi-kullandigi-iddiasi/
            # - https://teyit.org/pankartta-kahrolsun-seriat-basortusune-gecit-yok-yasasin-laiklik-yazdigi-iddiasi/
            # - https://teyit.org/a-haberin-muharrem-ince-icin-universiteyi-8-donemde-bitirmis-alt-bandi-kullandigi-iddiasi/
            # - https://teyit.org/adalet-partisi-genel-baskani-vecdet-ozun-tayyip-size-mustahak-dedigi-iddiasi/
            continue
        claim_reviews.extend(claim_review)

    utils.write_json_with_path(claim_reviews, my_path, 'claimReviews.json')

def scrape_all():
    all_urls = get_all_articles_url()
    get_claim_reviews(all_urls)

def main():
    scrape_all()

if __name__ == '__main__':
    logger.APP_LOGGER.info(f'Collecting false claims from teyit.org')
    collect_claims('yanlis')
    # test()
