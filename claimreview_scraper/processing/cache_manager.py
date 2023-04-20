"""
this module caches all the web GET requests using the mongo collection "cache".
"""

import requests

from . import unshortener
from . import database_builder


def get(url: str, unshorten=True, force_refresh=False, verify=True, headers={}) -> str:
    """
    Get the HTML of a URL, either from cache or from the web.

    Args:
        url (str): the URL to get
        unshorten (bool): whether to unshorten the URL first
        force_refresh (bool): whether to force a refresh of the cache
        verify (bool): whether to verify SSL certificates
        headers (dict): headers to send with the request

    Returns:
        str: the HTML of the URL
    """
    if unshorten:
        url_short = url
        url = unshortener.unshorten(url_short)
    cache_hit = database_builder.cache_get(url)
    if cache_hit and not force_refresh:
        # cached
        return cache_hit["html"]
    else:
        # new
        response = requests.head(url, headers=headers, verify=verify, timeout=20)
        if int(response.headers.get("content-length", 0)) > 10000000:
            # too large
            return "TOO LARGE"
        response = requests.get(url, headers=headers, verify=verify, timeout=20)
        if response.status_code != 200:
            print("WARN", response.status_code, "for", url)
        html = response.text
        database_builder.cache_put(url, html)
        return html
