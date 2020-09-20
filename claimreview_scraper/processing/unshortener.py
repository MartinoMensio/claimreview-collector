"""This unshortener relies on the backend"""

import requests

# endpoint = 'https://misinfo.me/misinfo/api/utils/unshorten'
endpoint = 'http://localhost:5000/misinfo/api/utils/unshorten'

def unshorten(url):
    try:
        res = requests.get(endpoint, params={'url': url})
        res.raise_for_status()
        result = res.json()
        return result['url_full']
    except Exception as e:
        print(e, url)
        raise ValueError(url)



def main():
    # with open('data/aggregated_urls.json') as f:
    #     data = json.load(f)
    # urls = data.keys()
    # unshorten_multiprocess(urls)
    unshorten('http://bit.ly/rR1us')
