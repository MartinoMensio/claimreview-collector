import os
import json
import multiprocessing
import requests
import time
import tqdm
import signal
import sys
import validators

from bs4 import BeautifulSoup

import database_builder

resolver_url = 'https://unshorten.me/'

class Unshortener(object):
    def __init__(self):
        self.session = requests.Session()
        res_text = self.session.get(resolver_url).text
        soup = BeautifulSoup(res_text, 'html.parser')
        csrf = soup.select('input[name="csrfmiddlewaretoken"]')[0]['value']
        #print(csrf)
        self.csrf = csrf

    def unshorten(self, url, handle_error=True):
        source_url = database_builder.get_url_redirect(url)
        if source_url:
            source_url = source_url['to']
        else:
            res_text = self.session.post(resolver_url, headers={'Referer': resolver_url}, data={'csrfmiddlewaretoken': self.csrf, 'url': url}).text
            soup = BeautifulSoup(res_text, 'html.parser')
            try:
                source_url = soup.select('section[id="features"] h3 code')[0].get_text()
            except:
                print('ERROR for', url)
                if handle_error:
                    source_url = url
                else:
                    source_url = None
            checked_url = clear_url(url)
            checked_source_url = clear_url(source_url)
            if checked_url and checked_source_url:
                database_builder.load_url_redirect(url, source_url)

        return source_url

def clear_url(url):
    url = url[:1000] # mongo limit
    if validators.url(url) == True:
        return url
    else:
        return None

def func(params):
    url, uns = params
    res = uns.unshorten(url)
    #print(res)
    return (url, res)

def unshorten_multiprocess(url_list, pool_size=4):
    # one unshortener for each process
    unshorteners =  [Unshortener() for _ in range(pool_size)]
    args = [(url, unshorteners[idx % pool_size]) for (idx,url) in enumerate(url_list)]
    with multiprocessing.Pool(pool_size) as pool:
        # one-to-one with the url_list
        specific_results = {}
        for result in tqdm.tqdm(pool.imap_unordered(func, args), total=len(args)):
            url, resolved = result
            database_builder.load_url_redirect(url, resolved)
            specific_results[url] = resolved
    return specific_results



if __name__ == "__main__":
    unshorten_multiprocess(urls)