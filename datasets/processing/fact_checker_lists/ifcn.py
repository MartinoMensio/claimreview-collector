import requests
from bs4 import BeautifulSoup

from .. import utils

# TODO scrape the compliances from https://ifcncodeofprinciples.poynter.org/know-more/what-it-takes-to-be-a-signatory

my_path = utils.data_location / 'ifcn'


def colors_to_value(style_str):
    color_map = {
        '#4caf50': 'fully_compliant',
        '#03a9f4': 'partially_compliant',
        '#fff': 'empty',
        '#f44336': 'none_compliant'
    }
    for k, v in color_map.items():
        if k in style_str:
            return v
    raise ValueError(style_str)


def extract_signatory_info(detail_url):
    print(detail_url)
    response = requests.get(detail_url)
    if response.status_code != 200:
        print('error retrieving {}'.format(detail_url))
        raise ValueError(response.status_code)

    soup = BeautifulSoup(response.text, 'lxml')

    id = detail_url.split('/')[-1]
    name = None
    issued_on = None
    expires_on = None
    expired = None
    country = None
    language = None
    website = None
    skills = []

    card_bodies = soup.select('.card-body')
    for c in card_bodies:
        if 'Issued to' in c.text:
            name = c.text.replace('Issued to', '').strip()
        elif 'Issued on' in c.text:
            issued_on = c.text.replace('Issued on', '').strip()
        elif 'Expires on' in c.text:
            expires_on = c.text.replace('Expires on', '').strip()
            expired = '(Expired)' in expires_on
    details = soup.select('.col-xs-12.col-lg-3.py-1')
    for d in details:
        if 'Country:' in d.text:
            country = d.text.replace('Country:', '').strip()
        elif 'Language:' in d.text:
            language = d.text.replace('Language:', '').strip()
        elif 'Website:' in d.text:
            website = d.text.replace('Website:', '').strip()
    skills_elements = soup.select('.badge.badge-pill.badge-light.my-2.py-2')
    for s in skills_elements:
        skill_name = s.select('small b')[0].text
        circles = s.select('span.circle')
        values = [colors_to_value(c['style']) for c in circles]
        skills.append({'name': skill_name, 'values': values})
    result = {
        'id': id,
        'name': name,
        'issued_on': issued_on,
        'expires_on': expires_on,
        'expired': expired,
        'country': country,
        'language': language,
        'website': website,
        'skills': skills
    }
    print(result)
    return result


def get_signatories_info():
    source_url = 'https://ifcncodeofprinciples.poynter.org/signatories'

    response = requests.get(source_url)
    if response.status_code != 200:
        print('error retrieving list')
        raise ValueError(response.status_code)
    soup = BeautifulSoup(response.text, 'lxml')

    #card_body_containers = soup.select('.card div.card-body')
    #verified_signatories = card_body_containers[0]
    #expired_signatories = card_body_containers[1]

    result = []

    for signatory_el in soup.select('.card div.card-body div.media'):
        #url = signatory_el.select('a[title]')[0]['href']
        #name = signatory_el.select('div.media-body h5')[0].text.strip()
        #country = signatory_el.select('div.media-body h6')[0].text.strip().replace('from ', '')
        detail_url = signatory_el.select(
            'div.media-body div div div a')[0]['href']
        result.append(extract_signatory_info(detail_url))

    utils.write_json_with_path(result, my_path, 'ifcn_scraped.json')


def prepare_factcheckers():
    data = utils.read_json(my_path / 'ifcn_scraped.json')
    results = []
    for d in data:
        fc = {
            'name': d['name'],
            'url': d['website'],
            'description': '',
            'nationality': d['country'],
            'properties': d,
            'id': d['id'],
            'source': 'ifcn',
            'domain': utils.get_url_domain(d['website'])
        }
        fc['properties']['belongs_to_ifcn'] = True
        fc['properties']['valid'] = not d['expired']
        results.append(fc)

    utils.write_json_with_path(results, my_path, 'fact_checkers.json')

def main():
    get_signatories_info()
    prepare_factcheckers()
