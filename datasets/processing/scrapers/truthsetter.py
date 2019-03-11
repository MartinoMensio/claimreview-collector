# scraper for https://truthsetter.com/

import requests
from bs4 import BeautifulSoup

from .. import utils
from .. import claimreview

origin_url = 'https://truthsetter.com/api/news-feed/fact-checked'
fact_checking_base_url = 'https://metafact.io/factchecks/'
my_name = 'truthsetter'
my_location = utils.data_location / my_name


def main():
    response = requests.post(origin_url, data='{}').json()
    utils.write_json_with_path(response, my_location, 'scraped.json')
