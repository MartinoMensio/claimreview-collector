import os
import time
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import rdflib
from pyld import jsonld
import json

from ..processing import utils

subfolder_path = utils.data_location / 'esi_api'

def get_all_collection(collection_name):
    ESI_USER = os.environ['ESI_USER']
    ESI_PASS = os.environ['ESI_PASS']
    ESI_ENDPOINT = 'https://coinform.expertsystemcustomer.com/cc/api/v1/search'
    start = 0
    all_docs = []
    while True:
        params = {
            'collection': collection_name,
            'start': start,
            'q_schema_org_cr_n3':'*'
        }
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
        utils.write_json_with_path(response_json, subfolder_path / 'source', f'responses_{collection_name}_{start}.json')

        all_docs.extend(docs)
        start += len(docs)

    utils.write_json_with_path(all_docs, subfolder_path / 'source', f'docs_{collection_name}.json')

def read_docs():
    files = [subfolder_path / 'source' / 'docs_factcheckers.json', subfolder_path / 'source' / 'docs_fc-dev.json']

    all_docs = []
    for f_name in files:
        docs = utils.read_json(f_name)
        all_docs.extend(docs)

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



def main(scraping=False):
    if scraping:
        get_all_collection('factcheckers')
        get_all_collection('fc-dev')

    all_docs = read_docs()
    claimreviews = extract_claimreviews(all_docs)
    utils.write_json_with_path(claimreviews, subfolder_path, 'claimReviews.json')

if __name__ == "__main__":
    load_dotenv()
    main()