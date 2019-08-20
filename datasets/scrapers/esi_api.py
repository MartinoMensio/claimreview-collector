import os
import time
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

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
            # TODO filter only claimReview? &q_schema_org_cr_n3=* is not working!!!
        }
        response = requests.get(ESI_ENDPOINT, params=params, auth=HTTPBasicAuth(ESI_USER, ESI_PASS), verify=False)
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
        utils.write_json_with_path(docs, subfolder_path / 'source', f'responses_{collection_name}_{start}.json')

        all_docs.extend(docs)
        start += len(docs)

    utils.write_json_with_path(all_docs, subfolder_path / 'source', f'responses_{collection_name}.json')

def main():
    get_all_collection('factcheckers')
    get_all_collection('fc-dev')

if __name__ == "__main__":
    load_dotenv()
    main()