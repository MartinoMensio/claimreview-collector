# This scraper uses FlareSolverr to scrape from CloudFlare https://github.com/FlareSolverr/FlareSolverr

import requests


cloudflare_stuff = None

def get_cloudflare(url):
    global cloudflare_stuff
    # https://github.com/FlareSolverr/FlareSolverr
    if not cloudflare_stuff:
        res = requests.post('http://localhost:8191/v1', json={
            'cmd': 'sessions.create',
            'session': 'test'
        })
        res.raise_for_status()
        cloudflare_stuff = 'test'
    res = requests.post('http://localhost:8191/v1', json={
        'cmd': 'request.get',
        'session': 'test',
        'url': url,
        'maxTimeout': 60000
    })
    res.raise_for_status()
    content = res.json()
    if content['solution']['status'] not in [200, 404]:
        raise ValueError(content['solution']['status'])
    page = content['solution']['response']
    return page