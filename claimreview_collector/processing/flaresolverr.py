# This scraper uses FlareSolverr to scrape from CloudFlare https://github.com/FlareSolverr/FlareSolverr
import os
import requests

flaresolverr_host = os.environ.get("FLARESOLVERR_HOST", "localhost:8191")

cloudflare_stuff = None


def get_cloudflare(url, timeout=60):
    global cloudflare_stuff
    # https://github.com/FlareSolverr/FlareSolverr
    if not cloudflare_stuff:
        # res = requests.post(f'http://{flaresolverr_host}/v1', json={
        #     'cmd': 'sessions.create',
        #     'session': 'test'
        # })
        # res.raise_for_status()
        cloudflare_stuff = "test"
    res = requests.post(
        f"http://{flaresolverr_host}/v1",
        json={
            "cmd": "request.get",
            "session": "test",
            "url": url,
            "maxTimeout": timeout * 1000,
        },
    )
    print(res.json())
    res.raise_for_status()
    content = res.json()
    if content["solution"]["status"] not in [200, 404]:
        cloudflare_stuff = None
        # cloudflare catched us, try again
        raise ValueError(content["solution"]["status"])
    page = content["solution"]["response"]
    return page
