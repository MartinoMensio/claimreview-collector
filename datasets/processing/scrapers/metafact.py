# scraper for https://metafact.io/

import requests
from bs4 import BeautifulSoup

from .. import utils
from .. import claimreview

get_url = 'https://metafact.io/factchecks/load_factchecks?filter=popular&offset=0&limit=5000'
fact_checking_base_url = 'https://metafact.io/factchecks/'
my_name = 'metafact'
my_location = utils.data_location / my_name

labels_map = [
    'Not Enough Experts',
    'Affirmative',
    'Uncertain',
    'Negative'
]


def main():
    fact_checking_urls = []
    response = requests.get(get_url).json()
    utils.write_json_with_path(response, my_location, 'scraped.json')
    for el in response:
        description = el.get('description', None)
        soup = BeautifulSoup(description, 'lxml')
        claim_urls = soup.find_all('a')
        claim_urls = [el['href'] for el in claim_urls]
        label_original = labels_map[el['factcheck_status']]
        label = claimreview.simplify_label(label_original)
        fact_checking_urls.append({
            'url': '{}{}'.format(fact_checking_base_url, el['id']),
            'source': 'metafact',
            'title': el['question'],
            'subtitle': description,
            'claim_url': claim_urls,
            'label': label,
            'label_original': label_original
        })

    utils.write_json_with_path(fact_checking_urls, my_location, 'fact_checking_urls.json')