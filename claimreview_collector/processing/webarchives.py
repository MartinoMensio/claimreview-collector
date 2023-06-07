import re
from bs4 import BeautifulSoup
import requests

from . import utils
from . import flaresolverr


def permacc_resolve_url(url):
    match = re.match(r"https?://(www\.)?perma\.cc/(?P<perma_id>[^/]+)", url)
    perma_id = match.group("perma_id")
    url = f"https://perma.cc/api/v1/public/archives/{perma_id}/?format=json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    url_resolved = data["url"]
    return url_resolved


def archiveorg_resolve_url(url):
    match = re.match(
        r"^https?:\/\/web\.archive\.org.*\/(?P<original>https?:\/(?P<second_slash>\/)?.*)",
        url,
    )
    # TODO https://web.archive.org/web/20220224084547/%20https:/twitter.com/suriel/status/1496750577425997831
    if not match:
        # e.g. https://archive.org/details/FOXNEWSW_20220315_230000_Jesse_Watters_Primetime/start/672/end/732?q=happening
        print(url)
        return url
    original_url = match.group("original")
    second_slash = match.group("second_slash")
    if not second_slash:
        # double the //
        original_url = original_url[:6] + "/" + original_url[6:]
    return original_url


def archivetoday_resolve_url(url):
    # via normal request, you get the captcha page
    # response = requests.get(url)
    # response.raise_for_status()
    # soup = BeautifulSoup(response.text, 'lxml')

    # via cloudflare it works, no captcha
    try:
        text = flaresolverr.get_cloudflare(url, timeout=2)
        soup = BeautifulSoup(text, "lxml")

        domain = utils.get_url_domain(url)  # the specific archive.today domain
        original_url = soup.select_one(
            f'form[action="https://{domain}/search/"] input'
        )["value"]
        # long_link = soup.select_one('input#SHARE_LONGLINK')['value']
        # # parse page with beautifulsoup
        # # long_link = 'http://archive.today/2022.04.08-155753/https://t.me/neuesausrussland/3483' # TODO
        # # http://archive.today/2022.04.08-155753/https://t.me/neuesausrussland/3483
        # match = re.match(r'^https?:\/\/archive\.today.*\/(?P<original>https?:\/.*)', long_link)
        # original_url = match.group('original')
    except Exception as e:
        print("impossible to resolve URL", url, e)
        return url
    return original_url


domains = {
    "perma.cc": permacc_resolve_url,
    "archive.org": archiveorg_resolve_url,
    # .is, .li, .fo, .ph, .vn and .md (https://en.wikipedia.org/wiki/Help:Using_archive.today)
    "archive.today": archivetoday_resolve_url,
    "archive.ph": archivetoday_resolve_url,
    "archive.vn": archivetoday_resolve_url,
    "archive.is": archivetoday_resolve_url,
    "archive.li": archivetoday_resolve_url,
    "archive.fo": archivetoday_resolve_url,
    "archive.md": archivetoday_resolve_url,
    "archive.vn": archivetoday_resolve_url,
}


def resolve_url(url):
    domain = utils.get_url_domain(url)
    if domain not in domains:
        raise ValueError(f"Domain {domain} not supported by webarchives")
    try:
        return domains[domain](url)
    except Exception as e:
        print("resolve_url", e)
        return url
