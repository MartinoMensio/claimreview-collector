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
    # CDATA error
    page = re.sub('<!\[CDATA\[[\r\n]+[^\]]*[\r\n]+\]\]>', 'false', page)
    return page

def retrieve_claimreview(url):
    url_fixed = get_corrected_url(url)
    domain = utils.get_url_domain(url_fixed)
    parser = _domain_parser_map[domain]
    # download the page
    page_text = cache_manager.get(url_fixed, headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36'})
    page_text = fix_page(page_text)
    try:
        result = parser(page_text)
    except Exception as e:
        print(url)
        #print(page_text)
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
    itemReviewed = claimReview.get('properties', {}).get('itemReviewed', None)
    if itemReviewed:
        author = itemReviewed.get('properties', {}).get('author', None)
        if author:
            #exit(0)
            sameAs = author.get('properties', {}).get('sameAs', None)
            #if sameAs:
            #    print(sameAs)
            result = sameAs
    # TODO also return sameAs if present on the claim directly, other links there!!
    return result

def get_claim_rating(claimReview):
    # what to do with these labels? for now returns None so the claims are discarded
    # {'Known since 2008', 'Lacks context', 'Unproven claim', 'Tactics look typical', 'Cannot Be Verified', 'Shift from past position', 'Easily beats the market', 'Includes Hispanic Other Black', 'More words than action', 'By Some Counts Yes', 'Roe grants federal right', 'Not a Muslim migrant', 'Polls depend on wording', 'Had seat at table', "Record doesn't say that", 'Coverage has limits', 'Wrong', 'Not accurate', 'Photo is real', 'Misleads', 'Met half of them', 'Mostly entered before Obama', 'No evidence', 'Wrong use of word', 'Mis- leading', 'Lie of the Year', 'Other spending nears $200M', 'Too soon to say', 'Possible but risky', 'White House not studio', 'Obama Called in 2012', 'Trump ordered new probe', 'Disputed Claim', 'Clinton role still unclear', 'Flip- flop', 'False', 'They are not eligible', 'No such plan', 'Not what GM says', 'In dispute', 'Trump deserves some credit', 'Can still be deported', 'Spinning the facts', 'Revised after backlash', 'Personal tweet taken down', "It's Calif. law", "Japan's leader acted first", 'Mostly false', 'Study in Dispute', 'Salary not only factor', 'No contact', 'Needs Context', 'Old stat', "He's very close", 'Flip- Flop', 'Rates are even higher', 'Staff error', 'In effect since 1965', 'Far from clear', 'Number not that high', 'Claim omits key facts', "Didn't use that word", 'Ignores US GDP size', 'Needs context', 'U.S. has trade surplus', 'Depends on the metric', 'Not the Whole Story', 'Way early to say', 'Numbers are close', 'Trump role emerged later', 'Depends on source', 'No way to verify', 'Effect not clear', 'No way to know', 'Result of Trump policy', 'Twitter fixed a glitch', 'Ignores all tax hikes', 'Vetted by State Dept.', 'His numbers are outdated', 'Fuzzy math', 'Latino numbers much higher', 'Not the same thing', 'Not what Pelosi said', 'Not the whole story', 'Experts question wall impact', 'Flynn talked Russia sanction', 'Lacks Context', 'Under Dispute', 'Supports border tech security', 'Unlikely but possible', 'Could be much worse', 'Lacks Evidence', 'No MS-13 removal data', 'Legal rules unclear', 'She told law schools', 'Not Missouri students', "Don't count your chickens", 'Depends on intent', 'Not that clear cut', 'History poses big hurdle', 'But little impact yet'}
    rating = claimReview['properties']['reviewRating']
    try:
        best = int(rating['properties']['bestRating'])
        worst = int(rating['properties']['worstRating'])
        value = int(rating['properties']['ratingValue'])
        score = value / (best - worst)
    except:
        score = None
    if not score:
        # TODO map textual label to score
        #score = rating['properties']['alternateName']
        return None
        #raise NotImplementedError()
    return score




if __name__ == "__main__":
    res = plac.call(retrieve_claimreview)
    print(res)