"""This unshortener relies on the backend"""

import requests

# endpoint = 'https://misinfo.me/misinfo/api/utils/unshorten'
endpoint = 'http://localhost:5000/misinfo/api/utils/unshorten'

def unshorten(url):
    result = requests.get(endpoint, params={'url': url}).json()
    return result['url_full']



def main():
    # with open('data/aggregated_urls.json') as f:
    #     data = json.load(f)
    # urls = data.keys()
    # unshorten_multiprocess(urls)
    unshorten('http://bit.ly/rR1us')
