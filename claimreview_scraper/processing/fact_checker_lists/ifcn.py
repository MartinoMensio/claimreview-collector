import requests
from bs4 import BeautifulSoup

from .. import utils

# TODO scrape the compliances from https://ifcncodeofprinciples.poynter.org/know-more/what-it-takes-to-be-a-signatory

my_name = 'ifcn'

my_path = utils.data_location / my_name

source_url = 'https://ifcncodeofprinciples.poynter.org/signatories'

ifcn_domain = utils.get_url_domain(source_url)


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


def extract_signatory_info(detail_url, media_logo):
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
        'assessment_url': detail_url,
        'id': id,
        'name': name,
        'avatar': media_logo,
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
        media_logo = signatory_el.select_one('img.signatory-avatar')['src']
        result.append(extract_signatory_info(detail_url, media_logo))

    utils.write_json_with_path(result, my_path, 'ifcn_scraped.json')


def prepare_factcheckers():
    data = utils.read_json(my_path / 'ifcn_scraped.json')
    results = []
    for d in data:
        fc = {
            'assessment_url': d['assessment_url'],
            'name': d['name'],
            'description': '',
            'nationality': d['country'],
            'properties': d,
            'id': d['id'],
            'source': my_name,
            'url': d['website'],
            'domain': utils.get_url_domain(d['website']),
            'belongs_to_ifcn': True,
            'valid_ifcn': not d['expired'],
            'avatar': d['avatar']
        }
        results.append(fc)

    utils.write_json_with_path(results, my_path, 'fact_checkers.json')

"""
def get_graph_data():
    data = utils.read_json(my_path / 'fact_checkers.json')

    nodes = {}
    links = []
    node0 = {'id': ifcn_domain, 'type': 'source'}
    nodes[node0['id']] = node0
    for fc in data:
        link1 = {'from': ifcn_domain, 'to': fc['assessment_url'], 'type': 'publishes', 'credibility': 1.0, 'confidence': utils.relationships_default_confidences['publishes'], 'source': my_name}
        if fc['valid_ifcn']:
            credibility = 1.0
        else:
            credibility = 0.9
        #link2 = {'from': fc['assessment_url'], 'to': fc['url'], 'type': 'assesses', 'credibility': credibility, 'confidence': 1.0, 'source': my_name}
        #link3 = {'from': fc['url'], 'to': fc['domain'], 'type': 'published_by', 'credibility': 1.0, 'confidence': utils.relationships_default_confidences['published_by'], 'source': my_name}
        link23 = {'from': fc['assessment_url'], 'to': fc['domain'], 'type': 'assesses', 'credibility': 1.0, 'confidence': 1.0, 'source': my_name}
        node1 = {'id': fc['assessment_url'], 'type': 'document'}
        #node2 = {'id': fc['url'], 'type': 'document'}
        node3 = {'id': fc['domain'], 'type': 'source', 'avatar': fc['avatar']}

        for n in [node1, node3]:
            nodes[n['id']] = n

        for l in [link1, link23]:
            links.append(l)

    graph = {
        'nodes': nodes,
        'links': links
    }

    utils.write_json_with_path(graph, my_path, 'graph.json')
"""
def get_domain_data():
    data = utils.read_json(my_path / 'fact_checkers.json')
    assessments = []
    for fc in data:
        source = fc['assessment_url']
        fc_domain = fc['url']
        if fc['valid_ifcn']:
            credibility = 1.0
        else:
            credibility = 0.9
        assessments.append({
            'from': source,
            'to': fc_domain,
            'link_type': 'assesses',
            'credibility': credibility,
            'confidence': 1.0,
            'generated_by': my_name,
            'original_evaluation': fc['properties']
        })

    utils.write_json_with_path(assessments, my_path, 'domain_assessments.json')

def main():
    #get_signatories_info()
    prepare_factcheckers()
    get_domain_data()
