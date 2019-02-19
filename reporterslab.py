#!/usr/bin/env python

import requests
import plac
import pycountry
import unidecode

import utils
import unshortener

folder = utils.data_location / 'reporterslab'


def download_sheet():
    source_url = 'https://spreadsheets.google.com/feeds/list/10nFzJbHbPho7_kMFCRoX7VsQLSNIB3EaUh4ITDlsV0M/1/public/values?alt=json'

    request = requests.get(source_url)
    if request.status_code != 200:
        print('error retrieving list')
        exit()
    data = request.json()

    utils.write_json_with_path(data, folder / 'source', 'sheet.json')


def extract_list():
    data = utils.read_json(folder / 'source' / 'sheet.json')

    domains = []
    fact_checkers = []

    countries = pycountry.countries

    for row in data['feed']['entry']:
        country_name = row['gsx$country']['$t'].strip()
        name = row['gsx$name']['$t'].strip()
        url = row['gsx$url']['$t'].strip()
        ifcn = row['gsx$ifcncode']['$t'].strip()
        description = ''

        other_properties = {k[4:].replace('.', '_'): v['$t'] for k, v in row.items() if k.startswith('gsx$')}

        country_look_by = unidecode.unidecode(country_name)
        # manual fix for these
        if country_look_by == 'South Korea': country_look_by = 'Korea'
        if country_look_by == 'Czech Republic': country_look_by = 'Czechia'
        country = pycountry.countries.get(name=country_look_by)
        if not country:
            print('trying again for', country_look_by)
            country = next((c for c in countries if country_look_by in c.name), None)
        if country:
            country_code = country.alpha_2
        else:
            country_code = ''
            print(country_name)
            # and Kosovo is not in pycountry
            if country_look_by == 'Kosovo':
                country_code = 'XK'

        is_ifcn = ifcn == 'Verified Signatory'

        # match properties with IFCN
        if name == 'Liputan6 Cek Fakta': name = 'Liputan 6 - Cek Fakta'
        if name == 'Teyit': name = 'teyit.org'
        if name == 'Maldito Bulo ("Damned Hoax")': name = 'Maldito Bulo'
        # these two don't have a URL
        if name == 'El Poligrafo': url = 'https://poligrafo.sapo.pt/fact-checks'
        if name == 'Le Veritometre': url = 'http://itele.owni.fr/'

        # url = unshortener.unshorten(url)
        print(url)

        domains.append({
            'domain': url,
            'label': 'true',
            'source': 'reporterslab'
        })

        fact_checkers.append({
            'name': name,
            'url': url,
            'description': description,
            'nationality': country_code,
            'belongs_to_ifcn': is_ifcn,
            'properties': other_properties,
            'source': 'reporterslab',
            'domain': utils.get_url_domain(url)
        })

    utils.write_json_with_path(domains, folder, 'domains.json')
    utils.write_json_with_path(fact_checkers, folder, 'fact_checkers.json')


def main(download=False):
    if download:
        download_sheet()

    extract_list()

if __name__ == '__main__':
    plac.call(main)
