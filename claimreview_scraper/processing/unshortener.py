"""This unshortener relies on the backend or can be local"""

import requests
import os
import re
from urllib.parse import urlsplit, parse_qsl, quote, unquote, urlencode
from posixpath import normpath
import string

from . import utils, database_builder, webarchives

MISINFO_BACKEND = os.environ.get("MISINFO_BACKEND", "http://localhost:5000")


# endpoint = 'https://misinfo.me/misinfo/api/utils/unshorten'
endpoint = f"{MISINFO_BACKEND}/misinfo/api/utils/unshorten"


def unshorten_remote(url):
    try:
        res = requests.get(endpoint, params={"url": url})
        res.raise_for_status()
        result = res.json()
        return result["url_full"]
    except Exception as e:
        print(e, url)
        raise ValueError(url)


########################################
# BEGIN OF CODE FROM MISINFOME BACKEND #
########################################

SAFE_CHARS = "".join(
    [
        c
        for c in (string.digits + string.ascii_letters + string.punctuation)
        if c not in "%#"
    ]
)
VALID_DOMAIN = re.compile("^[a-zA-Z_\d-]{1,63}(\.[a-zA-Z\d-]{1,63})*$")


def escape(unescaped_str):
    unquoted = unquote(unescaped_str)
    while unquoted != unescaped_str:
        unescaped_str = unquoted
        unquoted = unquote(unquoted)
    return quote(unquoted, SAFE_CHARS)


shortening_domains = [
    # https://bit.do/list-of-url-shorteners.php
    "t.co",
    "bit.do",
    "lnkd.in",
    "db.tt",
    "qr.ae",
    "adf.ly",
    "goo.gl",
    "bitly.com",
    "curl.tv",
    "tinyurl.com",
    "ow.ly",
    "bit.ly",
    "ity.im",
    "q.gs",
    "is.gd",
    "po.st",
    "bc.vc",
    "twitthis.com",
    "u.to",
    "j.mp",
    "buzurl.com",
    "cutt.us",
    "u.bb",
    "yourls.org",
    "x.co",
    "prettylinkpro.com",
    "scrnch.me",
    "filoops.info",
    "vzturl.com",
    "qr.net",
    "1url.com",
    "tweez.me",
    "v.gd",
    "tr.im",
    "link.zip.net",
    "tinyarrows.com",
    "➡.ws",
    "/✩.ws",
    "vai.la",
    "go2l.ink",
    # others
    "lnkd.in",
    "cnn.it",
    "strw.rs",
    "nyer.cm",
    "bloom.bg",
    "n.pr",
    "soc.li",
    "wndw.ms",
    "amzn.com",
    "gph.is",
    "cs.pn",
    "fb.me",
    "cbr.st",
    "nzzl.us",
    "wp.me",
    "spr.ly",
    "spoti.fi",
    "g.co",
    "ht.ly",
    "rol.st",
    "rewirenews.link",
    "cwrld.us",
    "urbn.is",
    "ebks.to",
    "wrld.bg",
    "igg.me",
    "theatln.tc",
    "jrnl.ie",
    "go.shr.lc",
    "huff.to",
    "hvrd.me",
    "trib.al",
    "usaa.us",
    "instagr.am",
    "bzfd.it",
    "edwk.it",
    "interc.pt",
    "po.st",
    "nyti.ms",
    "wamu.fm",
    "t.co",
    "bos.gl",
    "dailyre.co",
    "sie.ag",
    "shrtm.nu",
    "econ.st",
    "capi.tl",
    "cbc.ca",
    "wrd.cm",
    "kck.st",
    "wapo.st",
    "imdb.me",
    "ln.is",
    "reut.rs",
    "wired.trib.al",
    "pw-ne.ws",
    "washex.am",
    "chroni.cl",
    "rviv.ly",
    "intel.ly",
    "nbcnews.to",
    "detne.ws",
    "is.gd",
    "dx.doi.org",
    "nyr.kr",
    "bonap.it",
    "snpy.tv",
    "brook.gs",
    "amzn.to",
    "amn.st",
    "ind.pn",
    "jwatch.us",
    "thesco.re",
    "mnky.in",
    "lat.ms",
    "ift.tt",
    "hill.cm",
    "gop.cm",
    "wbur.fm",
    "pwne.ws",
    "thetim.es",
    "ti.me",
    "scim.ag",
    "thkpr.gs",
    "shortyw.in",
    "tak.pt",
    "di.sn",
    "cbsn.ws",
    "dailym.ai",
    "engt.co",
    "bbc.in",
    "oxford.ly",
    "cfp.cc",
    "hub.am",
    "oe.cd",
    "lapl.me",
    "chn.ge",
    "aclj.us",
    "chng.it",
    "vult.re",
    "huffp.st",
    "awe.sm",
    "yhoo.it" "disq.us",
    "fxn.ws",
    "on.fb.me",
    "twb.ly",
    "mailchi.mp",
    "youtu.be",
    "db.tt",
    "conta.cc",
    "deck.ly",
    "smarturl.it",
    "virl.io",
    "ubm.io",
    "usat.ly",
    "bit.ly",
    "thedo.do",
    "soa.li",
    "adf.ly",
    "shar.es",
    "drudge.tw",
    "thebea.st" "pin.it",
    "wrld.at",
    "owl.li",
    "smithmag.co",
    "jstor.info",
    "fw.to",
    "cjr.bz" "meetu.ps",
    "abcn.ws",
    "bit.do",
    "poy.nu",
    "shr.gs",
    "etsy.me",
    "tech.mg",
    "edtru.st" "flip.it",
    "tgr.ph",
    "onforb.es",
    "edut.to",
    "redd.it",
    "apple.co",
    "apne.ws",
    "cnb.cx",
    "pens.pe" "wpo.st",
    "bfpne.ws",
    "slate.me",
    "long.fm",
    "ntrda.me",
    "tmblr.co",
    "cnet.co",
    "flic.kr",
    "ow.ly",
    "sco.lt",
    "some.ly",
    "bitly.com",
    "atxne.ws",
    "j.mp",
    "dlvr.it",
    "tcrn.ch",
    "goo.gl",
]


def unshorten_local(url, use_cache=True):
    """If use_cache is False, does not use the cache"""
    url_normalised = add_protocol(url)
    url_normalised = url_normalize(url_normalised)
    result = url_normalised
    # print('url_normalised', url_normalised)

    # to be tested
    # result = urlexpander.expand(result)
    # return result

    domain = utils.get_url_domain(url_normalised)
    if use_cache:
        cached = database_builder.get_url_redirect(url_normalised)
    else:
        cached = False
    if cached:
        # match found
        result = cached["to"]
        return result
    else:
        # not found
        # first of all, check if it is a webarchive url
        if domain in webarchives.domains:
            result = webarchives.resolve_url(url_normalised)
            if use_cache:
                database_builder.save_url_redirect(url_normalised, result)
        if domain in shortening_domains:
            try:
                res = requests.head(url_normalised, allow_redirects=True, timeout=2)
                result = res.url
            except requests.exceptions.Timeout as e:
                # website dead, return the last one
                result = e.request.url
            except requests.exceptions.InvalidSchema as e:
                # something like a ftp link that is not supported by requests
                error_str = str(e)
                found_url = re.sub(
                    "No connection adapters were found for '([^']*)'", r"\1", error_str
                )
                result = found_url
            except requests.exceptions.RequestException as e:
                # other exceptions such as SSLError, ConnectionError, TooManyRedirects
                if e.request and e.request.url:
                    result = e.request.url
                else:
                    # something is really wrong
                    print(e)
            except Exception as e:
                # something like http://ow.ly/yuFE8 that points to .
                print("error for", url)
            # result = remove_login_part(result)
            if use_cache:
                # save in the cache for next calls
                database_builder.save_url_redirect(url_normalised, result)
    return result


# def remove_login_part(url):
#     # facebook and instagram can have a login link with "next"
#     domain = utils.get_url_domain(url)
#     if domain == 'facebook.com':
#         url = url.replace('https://www.facebook.com/login.php?next=', '')


def add_protocol(url):
    """when the URL does not have http://"""
    if not re.match(r"[a-z]+://.*", url):
        # default protocol
        url = "https://" + url
    return url


def url_normalize(url):
    # print('url normalize called', url)
    url = url.replace("\t", "").replace("\r", "").replace("\n", "")
    url = url.strip()
    testurl = urlsplit(url)
    if testurl.scheme == "":
        url = urlsplit("http://" + url)
    elif testurl.scheme in ["http", "https"]:
        url = testurl
    else:
        return None

    scheme = url.scheme

    if url.netloc:
        try:
            hostname = url.hostname.rstrip(":")

            port = None
            try:
                port = url.port
            except ValueError:
                pass

            username = url.username
            password = url.password

            hostname = [part for part in hostname.split(".") if part]

            # # convert long ipv4
            # # here will fail domains like localhost
            # if len(hostname) < 2:
            #     hostname = [socket.inet_ntoa(struct.pack('!L', long(hostname[0])))]

            hostname = ".".join(hostname)
            # hostname = hostname.decode('utf-8').encode('idna').lower()

            if not VALID_DOMAIN.match(hostname):
                return None

        except:
            return None

        netloc = hostname
        if username:
            netloc = "@" + netloc
            if password:
                netloc = ":" + password + netloc
            netloc = username + netloc

        if port:
            if scheme == "http":
                port = "" if port == 80 else port
            elif scheme == "https":
                port = "" if port == 443 else port

            if port:
                netloc += ":" + str(port)

        path = netloc + normpath("/" + url.path + "/").replace("//", "/")
    else:
        return None

    query = parse_qsl(url.query, True)
    query = dict(query)
    # ignore tracking stuff
    query = {
        k: v
        for k, v in query.items()
        if k
        not in [
            "fbclid",
            "mc_cid",
            "mc_eid",
            "refresh_count",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
        ]
    }
    query = sorted(query.items())
    query = urlencode(query)

    fragment = url.fragment

    return ("%s://%s?%s#%s" % (scheme, escape(path), query, escape(fragment))).rstrip(
        "?#/ "
    )


######################################
# END OF CODE FROM MISINFOME BACKEND #
######################################


def unshorten(url, local=True):
    if local:
        return unshorten_local(url)
    else:
        return unshorten_remote(url)


def main():
    # with open('data/aggregated_urls.json') as f:
    #     data = json.load(f)
    # urls = data.keys()
    # unshorten_multiprocess(urls)
    unshorten("http://bit.ly/rR1us")
