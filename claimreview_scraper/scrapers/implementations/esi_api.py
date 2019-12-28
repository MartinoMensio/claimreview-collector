import os
import time
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import rdflib
from pyld import jsonld
import json

from .. import ScraperBase
from ...processing import database_builder
from ...processing import utils

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'esi_api'
        ScraperBase.__init__(self)
        # TODO set environment variables

    def scrape(self, update=False):
        # TODO set scraping to True when ESI dataset will be updated
        if update:
            database_builder.db[self.id].drop()
            self.get_all_collection('factcheckers')
            self.get_all_collection('fc-dev')

        all_docs = self.read_docs()
        claimreviews = extract_claimreviews(all_docs)
        database_builder.add_ClaimReviews(self.id, claimreviews)


    def get_all_collection(self, collection_name):
        ESI_USER = os.environ['ESI_USER']
        ESI_PASS = os.environ['ESI_PASS']
        ESI_ENDPOINT = 'https://coinform.expertsystemcustomer.com/cc/api/v1/search'
        start = 0
        all_docs = []
        first = True # if it is the first iteration or not
        while True:
            params = {
                'collection': collection_name,
                'start': start,
                'q_schema_org_cr_n3':'*'
            }
            # TODO the certificate verification has to be enabled!
            response = requests.get(ESI_ENDPOINT, params=params, auth=HTTPBasicAuth(ESI_USER, ESI_PASS), verify=False)
            print(response.url)
            if response.status_code == 429:
                print(response.text)
                print('sleeping for 1 minute')
                time.sleep(60)
                continue
            if response.status_code != 200:
                print(response.text)
                raise ValueError(response.status_code)

            response_json = response.json()
            docs = response_json['response']['docs']
            if not docs:
                break
            print(collection_name, start, len(docs))
            database_builder.save_original_data(self.id, docs, clean=False)

            all_docs.extend(docs)
            start += len(docs)
            first = False

        return all_docs

    def read_docs(self):
        all_docs = database_builder.get_original_data(self.id)
        all_docs = [el for el in all_docs]

        return all_docs

def extract_claimreviews(all_docs):
    #context = {"@vocab": "http://schema.org/"}
    context = {"@vocab": "http://schema.org/"}

    exception_count = 0
    results = []
    for d in all_docs:
        n3_field = d['schema_org_cr_n3']
        #n3_field = [el for el in n3_field if 'http://schema.org/ClaimReview' in el]
        # if len(n3_field) is not 1:
        #     raise ValueError(d['id'])
        try:
            n3_content = '\n'.join(n3_field)
            n3_str =  n3_content
            g = rdflib.Graph().parse(data=n3_str, format='n3')
            json_ld_str = g.serialize(format='json-ld')
            json_object = json.loads(json_ld_str)
            # framing is used to nest the different objects contained in @graph
            json_object = jsonld.frame(json_object, context)
            # how to remove other prefixes?
            # json_object = jsonld.frame(json_object, context, {'explicit':True})
            # compacting removes the prefixes
            json_object = jsonld.compact(json_object, context)

            claim_reviews_found = []
            for el in json_object['@graph']:
                if 'ClaimReview' in el.get('@type', ''):
                    filter_other_ns(el)
                    claim_reviews_found.append(el)
            if len(claim_reviews_found) != 1:
                print(len(claim_reviews_found), 'in', d['id'])
            results.extend(claim_reviews_found)
            # TODO need to avoid unnecessary nesting of fields (failing credibility import)
        except Exception as e:
            # TODO understand why KeyError 'http://schema.org/url'
            print('EXCEPTION GENERATED', d['id'], type(e), e)
            exception_count += 1


    print('stats:', len(all_docs), 'docs', len(results), 'claimReview extracted', exception_count, 'exceptions')
    return results

def filter_other_ns(obj):
    if isinstance(obj, list):
        for el in obj:
            filter_other_ns(el)
    elif isinstance(obj, dict):
        keys = [k for k in obj.keys()]
        for k in keys:
            if 'url' == k:
                # move up the URLs
                if '@id' in obj[k]:
                    obj[k] = obj[k]['@id']

            if 'https://' in k or 'http://' in k:
                #print(k)
                del obj[k]
            else:
                filter_other_ns(obj[k])



def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    load_dotenv()
    main()