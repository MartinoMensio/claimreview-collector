import requests
import MisinfoMe_datasets.datasets.processing.claimreview as claimreview
from bs4 import BeautifulSoup
from MisinfoMe_datasets.datasets import logger


def update_page_url(claim_label, page_no):
    return f"https://teyit.org/konu/analiz/{claim_label}/page/{page_no}"


def collect_claims(claim_label):
    page_no = 1

    page_url = update_page_url(claim_label, page_no)
    response = requests.get(page_url)

    cl_review= []

    while response.status_code != 404:
        soup = BeautifulSoup(response.content,'lxml')
        for article in soup.findAll('article'):
            if not article.select('div a'):
                logger.APP_LOGGER.info(f'{cl_review.count()} of {claim_label} claim is extracted.')
                break
            article_url = article.select('div a')[0]['href']
            cl_review = claimreview.retrieve_claimreview(article_url)
            print(cl_review)
        page_no = page_no + 1
        page_url = update_page_url(claim_label, page_no)
        response = requests.get(page_url)

def test():
    url = "https://teyit.org/a-haberin-chpnin-akil-almaz-nanoteknolojik-hilesi-alt-bandi-kullandigi-iddiasi/"
    print(claimreview.retrieve_claimreview(url))

if __name__ == '__main__':
    logger.APP_LOGGER.info(f'Collecting false claims from teyit.org')
    collect_claims('yanlis')
    # test()
