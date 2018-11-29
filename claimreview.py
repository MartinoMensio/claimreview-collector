import json
import extruct
#import requests
import plac
import re
from bs4 import BeautifulSoup

import utils
import unshortener
import cache_manager

def get_corrected_url(url):
    corrections = {
        'http://www.puppetstringnews.com/blog/obama-released-10-russian-agents-from-us-custody-in-2010-during-hillarys-uranium-deal': 'https://www.politifact.com/punditfact/statements/2017/dec/06/puppetstringnewscom/story-misleads-tying-obama-russian-spy-swap-hillar/',
        'http://static.politifact.com.s3.amazonaws.com/politifact/mugs/Noah_Smith_mug.jpg': 'https://www.politifact.com/punditfact/statements/2018/mar/08/noah-smith/has-automation-driven-job-losses-steel-industry/',
        'http://static.politifact.com.s3.amazonaws.com/politifact/mugs/NYT_TRUMP_CAMPAIGN_5.jpg': 'https://www.politifact.com/truth-o-meter/article/2017/feb/23/promises-kept-promises-stalled-rating-donald-trump/',
        'http://rebootillinois.com/2016/12/22/heres-one-place-indiana-illinois-workers-comp-laws-agree/': 'https://www.politifact.com/illinois/statements/2016/dec/19/david-menchetti/illinois-indiana-work-comp-law-same-words-differen/'
    }
    domain = utils.get_url_domain(url)
    if domain in ['bit.ly']:
        uns = unshortener.Unshortener()
        resolved = uns.unshorten(url)
        return resolved
    return corrections.get(url, url)

def fix_page(page):
    page = re.sub('"claimReviewed": ""([^"]*)""', r'"claimReviewed": "\1"', page)
    page = re.sub('}"itemReviewed"', '}, "itemReviewed"', page)
    return page

def retrieve_claimreview(url):
    url_fixed = get_corrected_url(url)
    domain = utils.get_url_domain(url_fixed)
    parser = _domain_parser_map[domain]
    # download the page
    page_text = cache_manager.get(url_fixed)
    page_text = fix_page(page_text)
    try:
        result = parser(page_text)
    except Exception as e:
        print(url)
        print(page_text)
        raise e
    return url_fixed, result

# the two main parsers: json_ld and html/sharethefacts
def _jsonld_parser(page):
    data = extruct.extract(page)
    json_lds = data['json-ld']
    claimReviews = [el for el in json_lds if 'ClaimReview' in el['@type']]
    return claimReviews

def _microdata_parser(page):
    #soup = BeautifulSoup(page, 'html.parser')
    #matches = soup.find_all('div', attrs={'itemtype': 'http://schema.org/ClaimReview'})
    #print(matches)
    #for m in matches:
    #
    data = extruct.extract(page)
    microdata = data['microdata']
    claimReviews = [el for el in microdata if 'ClaimReview' in el['type']]
    # TODO should divide @context and @type from type?
    return claimReviews

def _snopes_parser(page):
    return _jsonld_parser(page)

def _factcheck_parser(page):
    return _jsonld_parser(page)

def _politifact_parser(page):
    return _microdata_parser(page)

def _washingtonpost_parser(page):
    return _microdata_parser(page)

def _weeklystandard_parser(page):
    return _jsonld_parser(page)


_domain_parser_map = {
    'snopes.com': _snopes_parser,
    'www.snopes.com': _snopes_parser,
    'www.factcheck.org': _factcheck_parser,
    "www.politifact.com": _politifact_parser,
    'www.washingtonpost.com': _washingtonpost_parser,
    'www.weeklystandard.com': _weeklystandard_parser
}

def get_claim_urls(claimReview):
    result = None
    itemReviewed = claimReview.get('itemReviewed', None)
    if itemReviewed:
        author = itemReviewed.get('properties', {}).get('author', None)
        if author:
            print(author)
            #exit(0)
            sameAs = author.get('properties', {}, None).get('sameAs', None)
            result = sameAs

    return result

if __name__ == "__main__":
    res = plac.call(retrieve_claimreview)
    print(res)