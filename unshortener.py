"""This unshortener relies on the backend"""

import requests

endpoint = 'http://localhost:5000/misinfo/api/resolve_url'

def unshorten(url):
    result = requests.get(endpoint, params={'url': url}).json()

    return result



if __name__ == "__main__":
    # with open('data/aggregated_urls.json') as f:
    #     data = json.load(f)
    # urls = data.keys()
    # unshorten_multiprocess(urls)
    unshorten('http://bit.ly/rR1us')
