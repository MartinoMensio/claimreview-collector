import json
import extruct
#import requests
import plac
import re
import os
from bs4 import BeautifulSoup
import flatten_json
from tqdm import tqdm

from . import utils
from . import unshortener
from . import cache_manager

subfolder_path = utils.data_location / 'claimreviews'

# the values of truthiness for the simplified labels
simplified_labels_scores = {
    'true': 1.0,
    'mixed': 0.5,
    'fake': 0.0
}

credibility_score_from_label = lambda label: simplified_labels_scores[label] * 2 - 1.0

# simplified to the three cases true/mixed/fake
label_maps = {
    # from buzzface
    'mostly true': 'true',
    'mixture of true and false': 'mixed',
    'mostly false': 'fake',
    'no factual content': None,
    # from factcheckni
    'Accurate': 'true',
    #'Unsubstantiated': not true nor folse, no proofs --> discard
    'Inaccurate': 'fake',
    # from mrisdal, opensources, pontes_fakenewssample
    'fake': 'fake',
    'bs': 'fake',
    'bias': 'fake',
    'conspiracy': 'fake',
    'junksci': 'fake',
    #'hate': 'fake', # hate speech is not necessarily fake
    'clickbait': 'fake',
    #'unreliable': 'fake',
    'reliable': 'true',
    'conspirancy': 'fake',
    # from leadstories
    'Old Fake News': 'fake',
    'Fake News': 'fake',
    'Hoax Alert': 'fake',
    # from politifact
    'False': 'fake',
    'True': 'true',
    'Mostly True': 'true',
    'Half True': 'mixed',
    'Half-True': 'mixed',
    'Mostly False': 'fake',
    'Pants on Fire!': 'fake',
    # from golbeck_fakenews
    'Fake': 'fake',
    # from liar (politifact-dashed)
    'false': 'fake',
    'true': 'true',
    'mostly-true': 'true',
    'mostly-false': 'fake',
    'barely-true': 'fake',
    'pants-fire': 'fake',
    'half-true': 'mixed',
    # from vlachos_factchecking
    'TRUE': 'true',
    'FALSE': 'fake',
    'MOSTLY TRUE': 'true',
    'MOSTLY FALSE': 'fake',
    'HALF TRUE': 'mixed',
    # others from ClaimReviews
    'Accurate': 'true',
    'Inaccurate': 'fake',
    'Wrong': 'fake',
    'Not accurate': 'fake',
    'Lie of the Year': 'fake',
    'Mostly false': 'fake',
    # metafact.ai labels
    'Affirmative': 'true',
    'Negative': 'fake',
    'Uncertain': 'mixed',
    #'Not Enough Experts': ??
}


def get_corrected_url(url, resolve=True):
    #url = re.sub(r'http://(punditfact.com)/(.*)', r'https://politifact.com/\2', url)
    corrections = {
        'http://www.puppetstringnews.com/blog/obama-released-10-russian-agents-from-us-custody-in-2010-during-hillarys-uranium-deal': 'https://www.politifact.com/punditfact/statements/2017/dec/06/puppetstringnewscom/story-misleads-tying-obama-russian-spy-swap-hillar/',
        'http://static.politifact.com.s3.amazonaws.com/politifact/mugs/Noah_Smith_mug.jpg': 'https://www.politifact.com/punditfact/statements/2018/mar/08/noah-smith/has-automation-driven-job-losses-steel-industry/',
        'http://static.politifact.com.s3.amazonaws.com/politifact/mugs/NYT_TRUMP_CAMPAIGN_5.jpg': 'https://www.politifact.com/truth-o-meter/article/2017/feb/23/promises-kept-promises-stalled-rating-donald-trump/',
        'http://rebootillinois.com/2016/12/22/heres-one-place-indiana-illinois-workers-comp-laws-agree/': 'https://www.politifact.com/illinois/statements/2016/dec/19/david-menchetti/illinois-indiana-work-comp-law-same-words-differen/'
    }
    resolved = corrections.get(url, url)
    if resolve:
        resolved = unshortener.unshorten(resolved)
    return resolved

def fix_page(page):
    page = re.sub('"claimReviewed": ""([^"]*)"', r'"claimReviewed": "\1', page)
    page = re.sub('}"itemReviewed"', '}, "itemReviewed"', page)
    # Politifact broken http://www.politifact.com/north-carolina/statements/2016/mar/30/pat-mccrory/pat-mccrory-wrong-when-he-says-north-carolinas-new
    page = re.sub('" "twitter": "', '", "twitter": "', page)
    # CDATA error
    page = re.sub('<!\[CDATA\[[\r\n]+[^\]]*[\r\n]+\]\]>', 'false', page)
    return page

def retrieve_claimreview(url):
    # url_fixed = get_corrected_url(url)
    url_fixed = url
    domain = utils.get_url_domain(url_fixed)
    try:
        parser = _domain_parser_map[domain]
    except Exception as e:
        print(domain, url, url_fixed)
        raise e
    # download the page
    page_text = cache_manager.get(url_fixed, headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36', 'Cookie': 'wp_gdpr=1|1;'})
    page_text = fix_page(page_text)
    try:
        result = parser(page_text)
    except Exception as e:
        print(url)
        raise e
    return url_fixed, result

# the two main parsers: json_ld and html/sharethefacts
def _jsonld_parser(page):
    data = extruct.extract(page)
    json_lds = data['json-ld']
    claimReviews = [el for el in json_lds if 'ClaimReview' in el.get('@type', '')]
    return claimReviews

def _microdata_parser(page):
    #soup = BeautifulSoup(page, 'html.parser')
    #matches = soup.find_all('div', attrs={'itemtype': 'http://schema.org/ClaimReview'})
    #print(matches)
    #for m in matches:
    #
    data = extruct.extract(page)
    # filter before flattening otherwise merge errors
    microdata = [el for el in data['microdata'] if el['type'] == 'http://schema.org/ClaimReview']
    jsonld = _to_jsonld(microdata)
    # get only the ClaimReview, not other microdata
    claimReviews = [el for el in jsonld if ('@type' in el and 'ClaimReview' in el['@type'])]
    return claimReviews

def _fake_parser(page):
    return []

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
    'www.weeklystandard.com': _weeklystandard_parser,
    'hoax-alert.leadstories.com': _jsonld_parser,
    'teyit.org': _jsonld_parser,
    'fullfact.org': _jsonld_parser,
    'chequeado.com': _jsonld_parser,
    'nytimes.com': _jsonld_parser,
    'www.nytimes.com': _jsonld_parser,
    'factcheck.afp.com': _jsonld_parser,
    'www.animalpolitico.com': _microdata_parser,
    # without claimReview
    'newtral.es': _fake_parser,
    'factcheckni.org': _fake_parser,
    'www.lemonde.fr': _fake_parser,
    'verafiles.org': _fake_parser
}

def clean_claim_url(url):
    result = url
    # remove the "mm:ss mark of URL" that is used for some videos
    if result:
        result = re.sub(r'.*\s+mark(\sof)?\s+(.+)', r'\2', result)
        domain = utils.get_url_domain(result)
        # some sameAs point to wikipedia page of person/organisation
        if re.match(r'.*wikipedia\.org', domain):
            result = None
        # some sameAs point to twitter.com/screen_name and not to twitter.com/screen_name/status
        elif re.match(r'https?://(www.)?twitter\.com/[^/]*/?', result):
            result = None
    return result

def get_claim_urls(claimReview):
    result = None
    itemReviewed = claimReview.get('itemReviewed', None)
    if not itemReviewed:
        itemReviewed = claimReview.get('properties', {}).get('itemReviewed', None)
    if itemReviewed:
        appearance = itemReviewed.get('appearance', None)
        if appearance:
            # new field appearance in https://pending.schema.org/Claim
            result = appearance[0]['url']
        else:
            sameAs = itemReviewed.get('sameAs', None)
            if sameAs:
                result = itemReviewed['sameAs']
            else:
                author = itemReviewed.get('author', None)
                if not author:
                    author = itemReviewed.get('properties', {}).get('author', None)
                if author:
                    #exit(0)
                    sameAs = author.get('sameAs', None)
                    if not sameAs:
                        sameAs = author.get('properties', {}).get('sameAs', None)
                    #if sameAs:
                    #    print(sameAs)
                result = sameAs
    # TODO also return sameAs if present on the claim directly, other links there!!
    if type(result) == list:
        # TODO consider multiple values
        result = clean_claim_url(result[0])
    else:
        result = clean_claim_url(result)
    return result

def get_claim_rating(claimReview):
    # what to do with these labels? for now returns None so the claims are discarded
    # {'Known since 2008', 'Lacks context', 'Unproven claim', 'Tactics look typical', 'Cannot Be Verified', 'Shift from past position', 'Easily beats the market', 'Includes Hispanic Other Black', 'More words than action', 'By Some Counts Yes', 'Roe grants federal right', 'Not a Muslim migrant', 'Polls depend on wording', 'Had seat at table', "Record doesn't say that", 'Coverage has limits', 'Wrong', 'Not accurate', 'Photo is real', 'Misleads', 'Met half of them', 'Mostly entered before Obama', 'No evidence', 'Wrong use of word', 'Mis- leading', 'Lie of the Year', 'Other spending nears $200M', 'Too soon to say', 'Possible but risky', 'White House not studio', 'Obama Called in 2012', 'Trump ordered new probe', 'Disputed Claim', 'Clinton role still unclear', 'Flip- flop', 'False', 'They are not eligible', 'No such plan', 'Not what GM says', 'In dispute', 'Trump deserves some credit', 'Can still be deported', 'Spinning the facts', 'Revised after backlash', 'Personal tweet taken down', "It's Calif. law", "Japan's leader acted first", 'Mostly false', 'Study in Dispute', 'Salary not only factor', 'No contact', 'Needs Context', 'Old stat', "He's very close", 'Flip- Flop', 'Rates are even higher', 'Staff error', 'In effect since 1965', 'Far from clear', 'Number not that high', 'Claim omits key facts', "Didn't use that word", 'Ignores US GDP size', 'Needs context', 'U.S. has trade surplus', 'Depends on the metric', 'Not the Whole Story', 'Way early to say', 'Numbers are close', 'Trump role emerged later', 'Depends on source', 'No way to verify', 'Effect not clear', 'No way to know', 'Result of Trump policy', 'Twitter fixed a glitch', 'Ignores all tax hikes', 'Vetted by State Dept.', 'His numbers are outdated', 'Fuzzy math', 'Latino numbers much higher', 'Not the same thing', 'Not what Pelosi said', 'Not the whole story', 'Experts question wall impact', 'Flynn talked Russia sanction', 'Lacks Context', 'Under Dispute', 'Supports border tech security', 'Unlikely but possible', 'Could be much worse', 'Lacks Evidence', 'No MS-13 removal data', 'Legal rules unclear', 'She told law schools', 'Not Missouri students', "Don't count your chickens", 'Depends on intent', 'Not that clear cut', 'History poses big hurdle', 'But little impact yet'}

    reviewRating = claimReview.get('reviewRating', None)
    if not reviewRating:
        reviewRating = claimReview.get('properties', {}).get('reviewRating', None)
    if not reviewRating:
        return None
    try:
        if 'properties' in reviewRating:
            reviewRating = reviewRating['properties']
        best = int(reviewRating['bestRating'])
        worst = int(reviewRating['worstRating'])
        value = int(reviewRating['ratingValue'])
        if best == -1 and worst == -1:
            score = None
        else:
            score = (value - worst) / (best - worst)
            # correct errors like: 'bestRating': '10', 'ratingValue': '0', 'worstRating': '1'
            score = min(score, 1.0)
            score = max(score, 0.0)
    except:
        score = None
    if not score:
        # TODO map textual label to score
        score = None
        try:
            scoreTxt = reviewRating.get('alternateName', None) or reviewRating.get('properties', {}).get('alternateName', None)
        except Exception as e:
            print(reviewRating)
            raise e
        simplified_label = simplify_label(scoreTxt)
        if simplified_label:
            score = simplified_labels_scores[simplified_label]
    return score

def get_label(claimReview):
    """get a label true/mixed/fake, very simplified"""
    score = get_claim_rating(claimReview)
    result = None
    if score != None:
        # convert to fake/true
        if score <= 0.30:
            result = 'fake'
        elif score >= 0.8:
            result = 'true'
        else:
            result = 'mixed'
    return result

def simplify_label(label):
    return label_maps.get(label, None)

def to_fact_checking_url(claimReview, source='claimReview'):
    if 'url' not in claimReview:
        print(claimReview)
        raise ValueError('missing URL')
    url = claimReview['url']
    claim_url = get_claim_urls(claimReview)
    if url == claim_url:
        print('same url and claim_url: {}'.format(url))
        claim_url = None
    return {
        'url': url,
        'source': source,
        'claim': claimReview.get('claimReviewed', None),
        'claim_url': claim_url,
        'label': get_label(claimReview),
        'date': claimReview.get('datePublished', None),
        'author': claimReview.get('author', {}).get('name', None)
    }

def _to_jsonld(microdata):
    context = 'http://schema.org'
    properties = 'properties_'
    typestr = 'type'
    jsonld_data = {}
    jsonld_data["@context"] = context
    for data in microdata:
        data = flatten_json.flatten(data)
        for key in data.keys():
            value = data[key]
            if context in value:
                value = value.replace(context+"/","")
            if(properties in key):
                keyn = key.replace(properties,"")
                jsonld_data[keyn] = value
                if(typestr in keyn):
                    keyn = keyn.replace(typestr,"@"+typestr)
                    jsonld_data[keyn] = value
            if(typestr is key):
                keyn = key.replace(typestr,"@"+typestr)
                jsonld_data[keyn] = value
        del data
    jsonld_data = flatten_json.unflatten(jsonld_data)
    return [jsonld_data]

"""
def get_claimreviews_from_factcheckers(original_claimreviews):
    result = []
    for idx, c in enumerate(tqdm(original_claimreviews)):
        c_full = get_claimreview_from_factcheckers(c)
        result.append(c_full)

    return result
"""

def get_claimreview_from_factcheckers(original_claimreview_url):
    """This method enriches a claimReview item with more data by going to the url of the publisher"""

    result = []

    # get the correct URL (some of them are wrong in the original dataset)
    fixed_url = get_corrected_url(original_claimreview_url)

    # this part with id and file saving is just to be able to restore the operation after a failure so that the single claims are saved onto disk on by one
    try:
        id = utils.string_to_md5(fixed_url)
        #print(id)
    except Exception as e:
        print(fixed_url)
        raise e
    partial_file_name = '{}.json'.format(id)
    partial_file_path = subfolder_path / partial_file_name
    #print(partial_file_name)
    if os.path.isfile(partial_file_path):
        # if it's been already saved, read it
        partial = utils.read_json(partial_file_path)
    else:
        # otherwise download the original claimReview from the fact checker
        try:
            url, partial = retrieve_claimreview(fixed_url)
            # and save it to disk
            utils.write_json_with_path(partial, subfolder_path, partial_file_name)
        except Exception as e:
            print(e)
            return result
    if not partial:
        # in this case there is no claimReview metadata on the fact checker website
        #print(c['url'])
        # return the original claimreview
        return []
    if len(partial):
        # there can be multiple claimReviews in a single fact checking page
        for j, claimReview in enumerate(partial):
            claimReview['url'] = fixed_url
            # save this in the result
            #result['{}::{}'.format(fixed_url, j)] = claimReview
            result.append(claimReview)

    return result

def extract_graph_edges(fact_checking_url):
    """TODO This function does not work, look at https://github.com/MartinoMensio/credibility_graph"""
    nodes = {}
    links = []

    for cr in fact_checking_url:
        claim_url = cr['claim_url']

        review_url = cr['url']
        reviewer_domain = utils.get_url_domain(review_url)

        nodes[review_url] = {'id': review_url, 'type': 'document'}
        nodes[reviewer_domain] = {'id': reviewer_domain, 'type': 'source'}

        link1 = {'from': reviewer_domain, 'to': review_url, 'type': 'publishes', 'credibility': 1.0, 'confidence': utils.relationships_default_confidences['publishes'], 'source': my_name}

        if claim_url:
            claim_domain = utils.get_url_domain(cu)
            nodes[cu] = {'id': cu, 'type': 'document'}
            nodes[claim_domain] = {'id': claim_domain, 'type': 'document'}

            label = cr['label']
            if label:
                if label == 'true':
                    truth_score = 1.0
                elif label == 'fake':
                    truth_score = 0.0
                else:
                    truth_score = 0.5
                credibility = truth_score * 2 - 1.0
            else:
                credibility = 0.0

            link2 = {'from': review_url, 'to': cu, 'type': 'reviews', 'credibility': credibility, 'confidence': utils.relationships_default_confidences['reviews'], 'source': my_name}
            link3 = {'from': cu, 'to': claim_domain, 'type': 'published_by', 'credibility': 1.0, 'confidence': utils.relationships_default_confidences['published_by'], 'source': my_name}

            # TODO add links to graph

    graph = {
        'nodes': nodes,
        'links': links
    }
    # TODO save graph
    return graph



def main():
    res = plac.call(get_claimreview_from_factcheckers)
    print(json.dumps(res))

if __name__ == "__main__":
    main()