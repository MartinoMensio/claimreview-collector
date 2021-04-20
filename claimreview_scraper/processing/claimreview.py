import json
import extruct
import requests
import plac
import re
import os
from bs4 import BeautifulSoup
import flatten_json
from tqdm import tqdm
import html

from . import utils
from . import unshortener
from . import cache_manager

# subfolder_path = 'data'# utils.data_location / 'claimreviews'

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
    'disinfo': 'fake'
}


def get_corrected_url(url, unshorten=False):
    #url = re.sub(r'http://(punditfact.com)/(.*)', r'https://politifact.com/\2', url)
    corrections = {
        'http://www.puppetstringnews.com/blog/obama-released-10-russian-agents-from-us-custody-in-2010-during-hillarys-uranium-deal': 'https://www.politifact.com/punditfact/statements/2017/dec/06/puppetstringnewscom/story-misleads-tying-obama-russian-spy-swap-hillar/',
        'http://static.politifact.com.s3.amazonaws.com/politifact/mugs/Noah_Smith_mug.jpg': 'https://www.politifact.com/punditfact/statements/2018/mar/08/noah-smith/has-automation-driven-job-losses-steel-industry/',
        'http://static.politifact.com.s3.amazonaws.com/politifact/mugs/NYT_TRUMP_CAMPAIGN_5.jpg': 'https://www.politifact.com/truth-o-meter/article/2017/feb/23/promises-kept-promises-stalled-rating-donald-trump/',
        'http://rebootillinois.com/2016/12/22/heres-one-place-indiana-illinois-workers-comp-laws-agree/': 'https://www.politifact.com/illinois/statements/2016/dec/19/david-menchetti/illinois-indiana-work-comp-law-same-words-differen/',
        'in an ad': 'https://www.politifact.com/ohio/statements/2016/may/13/fighting-ohio-pac/fighting-ohio-pac-ad-takes-ted-stricklands-mixed-a/',
        'https://hingtonpost.com/news/fact-checker/wp/2016/09/15/clintons-claim-that-its-legal-for-workers-to-be-retaliated-against-for-talking-about-their-pay/': 'https://www.washingtonpost.com/news/fact-checker/wp/2016/09/15/clintons-claim-that-its-legal-for-workers-to-be-retaliated-against-for-talking-about-their-pay/',
    }
    unshortened = corrections.get(url, url)
    if unshorten:
        unshortened = unshortener.unshorten(unshortened)
    return unshortened

def fix_page(page):
    # page = re.sub('"claimReviewed": ""([^"]*)"', r'"claimReviewed": "\1"', page)
    page = re.sub('"claimReviewed": "(.*)",', r'"claimReviewed": "\1",', page)
    page = re.sub('}"itemReviewed"', '}, "itemReviewed"', page)
    # Politifact broken http://www.politifact.com/north-carolina/statements/2016/mar/30/pat-mccrory/pat-mccrory-wrong-when-he-says-north-carolinas-new
    page = re.sub('" "twitter": "', '", "twitter": "', page)
    # CDATA error
    page = re.sub('<!\[CDATA\[[\r\n]+[^\]]*[\r\n]+\]\]>', 'false', page)
    # fixing double quote
    # page = re.sub(r'("[^"]+":\s+")(.*)"', lambda x: '{}{}"'.format(x.group(1), x.group(2).replace('"', "''")), page)
    # try:
    #     result = re.search('claimReviewed": "(.*)",', page, re.UNICODE | re.IGNORECASE)
    #     if result is not None:
    #         double_quoted = result.group(1)
    #         print(double_quoted)
    #         double_quoted_fixed = double_quoted.replace('"', '\'\'')
    #         page = page.replace(double_quoted, double_quoted_fixed)
    # except AttributeError as e:
    #     print(e)

    return page

def retrieve_claimreview(url):
    result = []
    # url_fixed = get_corrected_url(url)
    url_fixed = url
    domain = utils.get_url_domain(url_fixed)
    # TODO: some websites use the @graph e.g.: https://factuel.afp.com/non-91-des-marocains-ne-sont-pas-prets-quitter-le-pays
    verify = True
    # these domain has SSL certificate that does not cover its own subdomain
    # ['live-video.leadstories.com', 'trending-gifs.leadstories.com', 'trending-videos.leadstories.com']
    if domain.endswith('leadstories.com'):
        verify = False
        domain = 'leadstories.com'
    try:
        parser = _domain_parser_map.get(domain, _jsonld_parser)
    except Exception as e:
        print(domain, url, url_fixed)
        raise e
    # download the page
    try:
        page_text = cache_manager.get(url_fixed, verify=verify, headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36', 'Cookie': 'wp_gdpr=1|1;'})
    # page_text = fix_page(page_text)
    except:
        print('unhandled exception downloading', url_fixed)
        return url, result
    try:
        result = parser(page_text)
    except json.decoder.JSONDecodeError:
        print('failed for', url, ' --> Trying with superpowers')
        pattern = re.compile('"claimReviewed": "(.*)",', re.UNICODE | re.MULTILINE)
        soup = BeautifulSoup(page_text, 'html.parser')
        matches = soup.find_all('script', attrs={'type': 'application/ld+json'})
        # probably the broken ClaimReview will be in matches[0], but double check
        # then here call the service to fix the json

        for match in matches:
            if "claimReviewed" in match.text:
                matchPatterns = re.findall(pattern, match.text)
                for matchPattern in matchPatterns:
                    matchPatternUpdated = matchPattern.replace('"', '\'\'')
                    page_text = match.text.replace(matchPattern,  matchPatternUpdated)
                    # docker run -dit --restart always --name dirtyjson-rest -p 12345:12345 martinomensio/dirtyjson
                    res = requests.post('http://localhost:12345', data=page_text.encode('utf-8'),
                                  headers={'content-type': 'text/plain'})
                    if res.status_code != 200:
                        result = [] # TODO fix logging
                    else:
                        result = [res.json()]
        print('superpowers worked!')
    except Exception as e:
        print("Unhandled error at", url)
        # raise e
        return url, result

    if not result:
        # try with sharethefacts widget scraping:
        # for (list avaliable here http://www.sharethefacts.org/about):
        # - PolitiFact # solution available from decoding https://static.politifact.com/js/sharethefacts-v1.js
        # - The Washington Post # seems not to have it (let's see)
        # - FactCheck.org # from https://dhpikd1t89arn.cloudfront.net/js/include/sharethefacts-v1.js but no page has it
        # - Gossip Cop
        # - Pagella Politica
        # - AGI
        # - La Stampa
        # - The Ferret
        # - ClimateFeedback
        # - Demagog
        # - NewsWeek
        # - Vera Files Fact Check
        # - BOOM
        # - Faktiskt

        # First find sharethefacts_id
        soup = BeautifulSoup(page_text, 'html.parser')
        a_hrefs = [el.get('href', '') for el in soup.select('a')]
        sharethefacts_microdata_embed_ids = [el.get('data-sharethefacts-uuid', None) for el in soup.select('div.sharethefacts_microdata_embed')]
        # some don't have the property...
        sharethefacts_microdata_embed_ids = [el for el in sharethefacts_microdata_embed_ids if el]
        sharethefacts_ids = [el.split('/')[-1] for el in a_hrefs if 'sharethefacts.co/share/' in el] + sharethefacts_microdata_embed_ids
        print(domain, 'sharethefacts_ids', sharethefacts_ids, url)
        if sharethefacts_ids:
            if domain in ['politifact.com','factcheck.org','washingtonpost.com','afp.com','tempo.co','pagellapolitica.it', 'demagog.org.pl', 'poynter.org', 'liberation.fr']:
                for el in sharethefacts_ids:
                    embed_url = f"https://dhpikd1t89arn.cloudfront.net/html-{el}.html"
                    response_text = cache_manager.get(embed_url)
                    # print(response.text)
                    try:
                        result = _jsonld_parser(response_text)
                    except Exception as e:
                        print('exception', e, 'at', embed_url)
                        result = []
                    # print(result)
            else:
                raise NotImplementedError(url_fixed)
    for r in result:
        r_url = r.get('url')
        if r_url != url_fixed:
            print('different ClaimReview.url. asked for:', url_fixed, 'and received:', r_url)
            r['url'] = url_fixed
    return url_fixed, result

# the two main parsers: json_ld and html/sharethefacts
def _jsonld_parser(page):
    data = extruct.extract(page, syntaxes=['json-ld'])
    json_lds = data['json-ld']
    if not json_lds:
        return []
    # print(json_lds)
    claimReviews = [el for el in json_lds if el.get('@type', '') and 'ClaimReview' in el.get('@type', '')]
    # print(claimReviews)
    return claimReviews

def _microdata_parser(page):
    #soup = BeautifulSoup(page, 'html.parser')
    #matches = soup.find_all('div', attrs={'itemtype': 'http://schema.org/ClaimReview'})
    #print(matches)
    #for m in matches:
    #
    data = extruct.extract(page, syntaxes=['microdata'])
    # filter before flattening otherwise merge errors
    microdata = [el for el in data['microdata'] if el['type'] == 'http://schema.org/ClaimReview']
    jsonld = _to_jsonld(microdata)
    # get only the ClaimReview, not other microdata
    claimReviews = [el for el in jsonld if ('@type' in el and 'ClaimReview' in el['@type'])]
    return claimReviews

def _fake_parser(page):
    return []


_domain_parser_map = {
    'snopes.com': _jsonld_parser,
    'www.snopes.com': _jsonld_parser,
    'www.factcheck.org': _jsonld_parser,
    'factcheck.org': _jsonld_parser,
    "www.politifact.com": _microdata_parser,
    "politifact.com": _microdata_parser,
    'www.washingtonpost.com': _microdata_parser,
    'washingtonpost.com': _microdata_parser,
    'www.weeklystandard.com': _jsonld_parser,
    'www.washingtonexaminer.com': _jsonld_parser,
    'leadstories.com': _jsonld_parser,
    # 'hoax-alert.leadstories.com': _jsonld_parser,
    # 'satire.leadstories.com': _jsonld_parser,
    # 'analysis.leadstories.com': _jsonld_parser,
    # 'politics.leadstories.com': _jsonld_parser,
    # 'entertainment.leadstories.com': _jsonld_parser,
    # 'live-video.leadstories.com': _jsonld_parser,
    # 'europe.leadstories.com': _jsonld_parser,
    # 'happening-now.leadstories.com': _jsonld_parser,
    # 'happening-now.leadstories.com': _jsonld_parser,
    # 'opinion.leadstories.com': _jsonld_parser,
    # 'tech.leadstories.com': _jsonld_parser,
    # 'trendolizer-picks.leadstories.com': _jsonld_parser,
    # 'trending-videos.leadstories.com': _jsonld_parser,
    # 'video.leadstories.com': _jsonld_parser,
    # 'movies.leadstories.com': _jsonld_parser,
    # 'trending-gifs.leadstories.com': _jsonld_parser,
    # 'donald-trump.leadstories.com': _jsonld_parser,
    # 'hillary-clinton.leadstories.com': _jsonld_parser,
    # 'hollywood-film-festival.leadstories.com': _jsonld_parser,
    # 'campaign-2016-trendolizer.leadstories.com': _jsonld_parser,
    # 'kardashian-trendolizer.leadstories.com': _jsonld_parser,
    # 'today-in-technology.leadstories.com': _jsonld_parser,
    # 'marilyn-monroe.leadstories.com': _jsonld_parser,
    # 'us-congress-news.leadstories.com': _jsonld_parser,
    # 'us-congress-news.leadstories.com': _jsonld_parser,
    'teyit.org': _jsonld_parser,
    'fullfact.org': _jsonld_parser,
    'chequeado.com': _jsonld_parser,
    'nytimes.com': _jsonld_parser,
    'www.nytimes.com': _jsonld_parser,
    'www.animalpolitico.com': _microdata_parser,
    'www.istinomer.rs': _microdata_parser,
    'kallxo.com': _jsonld_parser,
    'afp.com': _jsonld_parser,
    'u.afp.com': _jsonld_parser,
    'factcheck.afp.com': _jsonld_parser,
    'factuel.afp.com': _jsonld_parser,
    'factcheckthailand.afp.com': _jsonld_parser,
    'factcheck-adm.afp.com': _jsonld_parser,
    'healthfeedback.org': _jsonld_parser,
    'www.mm.dk': _jsonld_parser,
    'piaui.folha.uol.com.br': _jsonld_parser,
    'aosfatos.org': _jsonld_parser,
    'colombiacheck.com': _jsonld_parser,
    'www.boomlive.in': _jsonld_parser,
    'factcheck.kz': _jsonld_parser,
    'correctiv.org': _jsonld_parser,
    'www.vishvasnews.com': _jsonld_parser,
    'www.thequint.com': _jsonld_parser,
    'fit.thequint.com': _jsonld_parser,
    'dubawa.org': _jsonld_parser,
    'ghana.dubawa.org': _jsonld_parser,
    'faktograf.hr': _jsonld_parser,
    'www.indiatoday.in': _jsonld_parser,
    'observador.pt': _jsonld_parser,
    'nieuwscheckers.nl': _jsonld_parser,
    'factcheckni.org': _jsonld_parser,
    'pagellapolitica.it': _jsonld_parser,
    'demagog.org.pl': _jsonld_parser,
    'factly.in': _jsonld_parser,
    'poynter.org': _jsonld_parser,
    # without claimReview
    'newtral.es': _fake_parser,
    'www.newtral.es': _fake_parser,
    'www.lemonde.fr': _fake_parser,
    'verafiles.org': _fake_parser,
    'www.rappler.com': _fake_parser,
    'misbar.com': _fake_parser,
    'raskrinkavanje.ba': _fake_parser,
    'ici.radio-canada.ca': _fake_parser,
    'efectococuyo.com': _fake_parser,
    'www.buzzfeed.com': _fake_parser,
    'www.ellinikahoaxes.gr': _fake_parser,
    'www.francetvinfo.fr': _fake_parser,
    'www.cbc.ca': _fake_parser,
    'infact.press': _fake_parser,
    'www.sciencepresse.qc.ca': _fake_parser,
    'www.factcrescendo.com': _fake_parser,
    'english.factcrescendo.com': _fake_parser,
    'srilanka.factcrescendo.com': _fake_parser,
    'assamese.factcrescendo.com': _fake_parser,
    'factcheck.vlaanderen': _fake_parser,
    'tfc-taiwan.org.tw': _fake_parser,
    'politica.estadao.com.br': _fake_parser,
    'factcheck.aap.com.au': _fake_parser,
    'www.aap.com.au': _fake_parser,
    'www.ecuadorchequea.com': _fake_parser,
    'spondeomedia.com': _fake_parser,
    'cekfakta.tempo.co': _fake_parser,
    'www.facebook.com': _fake_parser,
    'observers.france24.com': _fake_parser,
    'mythdetector.ge': _fake_parser,
    'newsmobile.in': _fake_parser,
    # 's.id': _fake_parser, # shortener TODO
    # 'bit.ly': _fake_parser,
    'truthmeter.mk': _fake_parser,
    'vistinomer.mk': _fake_parser,
    'www.15min.lt': _fake_parser,
    'factcheck.ge': _fake_parser,
    'news.jtbc.joins.com': _fake_parser,
    'maldita.es': _fake_parser,
    'animal.mx': _fake_parser,
    'www.newschecker.in': _fake_parser,
    'lasillavacia.com': _fake_parser,
    'pesacheck.org': _fake_parser,
    'factnameh.com': _fake_parser,
    'www.delfi.lt': _fake_parser,
    'www.liberation.fr': _fake_parser,
    'www.youtube.com': _fake_parser,
    'medium.com': _fake_parser,
    'fatabyyano.net': _fake_parser,
    'www.efe.com': _fake_parser,
    'www.open.online': _fake_parser,
    'crithink.mk': _fake_parser,
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
        elif re.match(r'https?://(www.)?twitter\.com/[^/]*/?$', result):
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
        result = [clean_claim_url(el) for el in result]
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

# def get_claimreview_from_factcheckers(original_claimreview_url, ignore_cache=False):
#     """This method enriches a claimReview item with more data by going to the url of the publisher"""

#     result = []

#     # get the correct URL (some of them are wrong in the original dataset)
#     fixed_url = get_corrected_url(original_claimreview_url)

#     # this part with id and file saving is just to be able to restore the operation after a failure so that the single claims are saved onto disk on by one
#     try:
#         id = utils.string_to_md5(fixed_url)
#         #print(id)
#     except Exception as e:
#         print(fixed_url)
#         raise e
#     partial_file_name = '{}.json'.format(id)
#     partial_file_path = subfolder_path / partial_file_name
#     #print(partial_file_name)
#     if not ignore_cache and os.path.isfile(partial_file_path):
#         # if it's been already saved, read it
#         partial = utils.read_json(partial_file_path)
#     else:
#         # otherwise download the original claimReview from the fact checker
#         try:
#             url, partial = retrieve_claimreview(fixed_url)
#             # and save it to disk
#             utils.write_json_with_path(partial, subfolder_path, partial_file_name)
#         except Exception as e:
#             print(e)
#             return result
#     if not partial:
#         # in this case there is no claimReview metadata on the fact checker website
#         #print(c['url'])
#         # return the original claimreview
#         return []
#     if len(partial):
#         # there can be multiple claimReviews in a single fact checking page
#         for j, claimReview in enumerate(partial):
#             # the wrong claimReview.url needs to be fixed
#             claimReview['url'] = fixed_url
#             # save this in the result
#             #result['{}::{}'.format(fixed_url, j)] = claimReview
#             result.append(claimReview)

#     return result

