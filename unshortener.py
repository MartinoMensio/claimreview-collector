import os
import json
import multiprocessing
import requests
import time
import tqdm
import signal
import sys

from bs4 import BeautifulSoup

resolver_url = 'https://unshorten.me/'

class Unshortener(object):
    def __init__(self, mappings={}):
        self.session = requests.Session()
        res_text = self.session.get(resolver_url).text
        soup = BeautifulSoup(res_text, 'html.parser')
        csrf = soup.select('input[name="csrfmiddlewaretoken"]')[0]['value']
        #print(csrf)
        self.csrf = csrf
        self.mappings = mappings

    def unshorten(self, url):
        if url not in self.mappings:
            res_text = self.session.post(resolver_url, headers={'Referer': resolver_url}, data={'csrfmiddlewaretoken': self.csrf, 'url': url}).text
            soup = BeautifulSoup(res_text, 'html.parser')
            try:
                source_url = soup.select('section[id="features"] h3 code')[0].get_text()
            except:
                print('ERROR for', url)
                source_url = url
            m = (url, source_url)
            #print(m)
            self.mappings[m[0]] = m[1]
        else:
            source_url = self.mappings[url]
        return source_url

def func(params):
    url, uns = params
    res = uns.unshorten(url)
    #print(res)
    return (url, res)

def unshorten_multiprocess(url_list, mappings={}, pool_size=4):
    # one unshortener for each process
    unshorteners =  [Unshortener(mappings) for _ in range(pool_size)]
    args = [(url, unshorteners[idx % pool_size]) for (idx,url) in enumerate(url_list)]
    with multiprocessing.Pool(pool_size) as pool:
        all_res = {}
        for result in tqdm.tqdm(pool.imap_unordered(func, args), total=len(args)):
            url, resolved = result
            mappings[url] = resolved
    return mappings

mappings_file = 'data/mappings.json'
mappings = {}

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    with open(mappings_file, 'w') as f:
        mappings = json.dump(mappings, f, indent=2)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    with open('data/aggregated_urls.json') as f:
        data = json.load(f)
    urls = data.keys()
    if os.path.isfile(mappings_file):
        with open(mappings_file) as f:
            mappings = json.load(f)
    print('already mappings', len(mappings))
    try:
        unshorten_multiprocess(urls, mappings)
    except Exception as e:
        print('gotcha')
    with open(mappings_file, 'w') as f:
        mappings = json.dump(mappings, f, indent=2)