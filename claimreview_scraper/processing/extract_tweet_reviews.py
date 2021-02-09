'''
This script provides the 4500 tweet reviews dataset
'''

import os
import re
import tqdm
import json
import tldextract
import requests
from collections import defaultdict
from pathlib import Path

from . import utils, database_builder

TWITTER_CONNECTOR = os.environ.get('TWITTER_CONNECTOR', 'http://localhost:20200')
print('TWITTER_CONNECTOR', TWITTER_CONNECTOR)
MISINFO_BACKEND = os.environ.get('MISINFO_BACKEND', 'http://localhost:5000')
print('MISINFO_BACKEND', MISINFO_BACKEND)

client = database_builder.client
data_path = Path('data/latest')


# The following dicts are used to map the labels and the scores coming from the claimReviews

# the values of truthiness for the simplified labels in [0;1] range with None for 'not_verifiable'
simplified_labels_scores = {
    'credible': 1.0,
    'mostly_credible': 0.8,
    'uncertain': 0.5,
    'not_credible': 0.0,
    'not_verifiable': None
}
# simplified to the three cases true/mixed/fake
label_maps = {
    # from buzzface
    'mostly true': 'mostly_credible',
    'mixture of true and false': 'uncertain',
    'mostly false': 'not_credible',
    'no factual content': 'not_credible',
    # from factcheckni
    'Accurate': 'credible',
    'Unsubstantiated': 'not_verifiable', #not true nor false, no proofs
    'Inaccurate': 'not_credible',
    'inaccurate': 'not_credible',
    # from mrisdal, opensources, pontes_fakenewssample
    'fake': 'not_credible',
    'bs': 'not_credible', # bullshit
    'bias': 'uncertain',
    'conspiracy': 'not_credible',
    'junksci': 'not_credible',
    #'hate': 'fake', # hate speech is not necessarily fake
    'clickbait': 'not_credible',
    #'unreliable': 'fake',
    'reliable': 'credible',
    'conspirancy': 'not_credible',
    # from leadstories
    'Old Fake News': 'not_credible',
    'Fake News': 'not_credible',
    'Hoax Alert': 'not_credible',
    # from politifact
    'False': 'not_credible',
    'True': 'credible',
    'Mostly True': 'mostly_credible',
    'Half True': 'uncertain',
    'Half-True': 'uncertain',
    'Mostly False': 'not_credible',
    'Pants on Fire!': 'not_credible',
    'pants on fire': 'not_credible',
    'cherry picks': 'uncertain',
    # from golbeck_fakenews
    'Fake': 'not_credible',
    # from liar (politifact-dashed)
    'false': 'not_credible',
    'true': 'credible',
    'mostly-true': 'mostly_credible',
    'mostly-false': 'not_credible',
    'barely-true': 'uncertain',
    'pants-fire': 'not_credible',
    'half-true': 'uncertain',
    # from vlachos_factchecking
    'TRUE': 'credible',
    'FALSE': 'not_credible',
    'MOSTLY TRUE': 'mostly_credible',
    'MOSTLY FALSE': 'not_credible',
    'HALF TRUE': 'uncertain',
    # others from ClaimReviews
    'Accurate': 'credible',
    'Inaccurate': 'not_credible',
    'Wrong': 'not_credible',
    'Not accurate': 'not_credible',
    'Lie of the Year': 'not_credible',
    'Mostly false': 'not_credible',
    # metafact.ai labels
    'Affirmative': 'credible',
    'Negative': 'not_credible',
    'Uncertain': 'uncertain',
    'Not Enough Experts': 'not_verifiable',
    # tempo (indonesian)
    'BENAR' : 'credible',
    'SEBAGIAN BENAR' : 'uncertain',
    'TIDAK TERBUKTI' : 'uncertain', # unproven
    'SESAT' : 'uncertain', # facts are correct, but wrong conclusions (misleading)
    'KELIRU' : 'not_credible',
    'mixture': 'uncertain',
    'somewhat true': 'mostly_credible',
    'somewhat false': 'uncertain',
    'misleading': 'not_credible',
    'ambiguous': 'uncertain',
    # newtral.es
    'falso': 'not_credible',
    # verificat
    'fals': 'not_credible',
    # other things
    ': false': 'not_credible',
    ': true': 'credible',
    ': mixture': 'uncertain',
    'rating: false': 'not_credible',
    'rating by fact crescendo: false': 'not_credible',
    'verdadero': 'credible',
    'verdad a medias': 'uncertain',
    # factnameh
    '\u0646\u0627\u062f\u0631\u0633\u062a': 'not_credible', # false
    '\u0646\u06cc\u0645\u0647 \u062f\u0631\u0633\u062a': 'uncertain', # half true
    '\u06af\u0645\u0631\u0627\u0647\u200c\u06a9\u0646\u0646\u062f\u0647': 'not_credible', # misleading

    # fullfact (this is the beginning of the label, they have very long labels)
    'correct': 'credible',
    'that\u2019s correct': 'credible',
    'incorrect' : 'not_credible',
    'this is false': 'not_credible',
    'roughly correct': 'uncertain',
    'broadly correct': 'uncertain',
    'this isn\'t correct': 'not_credible',
    'this is correct': 'credible',
    'not far off': 'mostly_credible',
    'that\u2019s wrong': 'not_credible',
    'it\u2019s correct': 'credible',
    'this is true': 'credible',
    'this is wrong': 'not_credible',
    'that\'s correct': 'credible',
    'that is correct': 'credible',
    'these aren\u2019t all correct': 'uncertain',

    # teyit.org
    'yanliş': 'not_credible',
    'doğru': 'credible',
    'karma': 'uncertain',
    'belirsiz': 'not_verifiable', #'uncertain'

    # lemonde
    'faux': 'not_credible',

    # istinomer
    'neistina': 'not_credible',
    'skoro neistina': 'uncertain', # almost untrue

    # https://evrimagaci.org ???
    'sahte': 'not_credible',

    # https://verafiles.org
    'mali': 'not_credible',

    # poligrafo
    'verdadeiro': 'credible',
    'engañoso': 'not_credible', # misleading
    'contraditorio': 'uncertain', # contradictory

    # pagella politica
    'vero': 'credible',
    'c’eri quasi': 'mostly_credible', # almost true
    'c\'eri quasi': 'mostly_credible', # almost true
    'pinocchio andante': 'not_credible',
    'panzana pazzesca': 'not_credible',
    'nì': 'uncertain',

    # euvsdisinfo
    'disinfo': 'not_credible',


    # from twitter subset
    'Фейк': 'not_credible',
    # 'usatoday.com'
    'partly false': 'uncertain',
    # factcheck.org
    'baseless claim': 'not_verifiable',
    'mixed.': 'uncertain',
    'experts disagree': 'not_credible',
    'one pinocchio': 'mostly_credible',
    'two pinocchios': 'uncertain',
    'three pinocchios': 'not_credible',
    'four pinocchios': 'not_credible',
    'the statement is false': 'not_credible',
    'erroné': 'not_credible',
    'c\'est faux': 'not_credible',
    'not correct': 'not_credible',
    'not true': 'not_credible',
    'largely accurate': 'mostly_credible',
    'mixed': 'uncertain',
    'partially true': 'uncertain',
    'partly right': 'uncertain',


}





### UTILITIES
def write_json_with_path(content, path, filename, indent=2):
    """dump to json file, creating folder if necessary"""
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(path / filename, 'w') as f:
        json.dump(content, f, indent=indent)

def read_json(input_path):
    """read json from file"""
    with open(input_path) as f:
        return json.load(f)

def get_ifcn_domains():
    """get the list of domains of fact-checkers belonging to IFCN"""
    res = requests.get(f'{MISINFO_BACKEND}/misinfo/api/credibility/factcheckers')
    res.raise_for_status()
    signatories = res.json()
    
    write_json_with_path(signatories, data_path, 'ifcn_sources.json')
    ass = {el['domain']: el for el in signatories}
    # print(ass)
    print('there are', len(ass), 'ifcn trusted domains')
    return ass


### MAPPING FUNCTIONS

def claimreview_get_coinform_label(cr):
    """takes a ClaimReviews and outputs a CoInform score"""
    # unify to the score (easier to work with numbers)
    score = claimreview_get_rating(cr)
    # and then map the score to the labels
    mapped_label = get_coinform_label_from_score(score)
    return mapped_label

def simplify_label(label):
    """maps from the fact-checker label to the coinform label"""
    # normalise string to lowercase and strip spaces around
    label = label.strip().lower()
    label = label.replace('fact crescendo rating: ', '')
    label = label.replace('fact crescendo rating - ', '')
    label = label.replace('fact crescendo rating ', '')
    # first look for the full label
    result = label_maps.get(label, None)
    # then if the label begins with something known
    if not result:
        for k,v in label_maps.items():
            if label.startswith(k.lower()):
                result = v
                break
    if not result:
        # return None which will get mapped
        pass
    return result

def claimreview_get_rating(claimreview):
    """takes a claimReviews and outputs a score of truthfulness between [0;1] or None if not verifiable"""
    # take the reviewRating
    reviewRating = claimreview.get('reviewRating', None)
    if not reviewRating:
        # sometimes reviewRating is inside "properties"
        reviewRating = claimreview.get('properties', {}).get('reviewRating', None)
    if not reviewRating:
        # nothing to say
        return None
    

    if 'properties' in reviewRating:
        reviewRating = reviewRating['properties']

    score = None

    # first take the textual label
    try:
        scoreTxt = reviewRating.get('alternateName', '') or reviewRating.get('properties', {}).get('alternateName', '')
        if isinstance(scoreTxt, dict):
            scoreTxt = scoreTxt['@value']
    except Exception as e:
        print(reviewRating)
        raise e
    try:
        # map it to the coinform labels
        simplified_label = simplify_label(scoreTxt)
    except Exception as e:
        print(claimreview['url'])
        print(reviewRating)
        raise e
    if simplified_label:
        # get the numerical score
        score = simplified_labels_scores[simplified_label]

    # second strategy: if the textual label is unknown, take the rating value
    if score == None:
        try:
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
        except Exception as e:
            # in the case the numbers are not found, there is not any information that can be used to map the rating
            score = None

    return score

def get_coinform_label_from_score(score):
    """The inverse function of `simplified_labels_scores`"""
    if score is None:
        return 'not_verifiable'
    if score > 0.8:
        return 'credible'
    if score > 0.6:
        return 'mostly_credible'
    if score > 0.4:
        return 'uncertain'
    return 'not_credible'

def claimreview_get_claim_appearances(claimreview):
    """from a `ClaimReview`, get all the URLs mentioned as appearances"""
    try:
        factchecker_url = claimreview['url']
        factchecker_domain = utils.get_url_domain(factchecker_url)
        result = []
        itemReviewed = claimreview.get('itemReviewed', None)
        if not itemReviewed:
            itemReviewed = claimreview.get('properties', {}).get('itemReviewed', None)
        if itemReviewed:
            # sometimes the appearances are stored in the correct place
            appearance = itemReviewed.get('appearance', [])
            if isinstance(appearance, str):
                # checkyourfact.com sometimes just puts the url as string
                appearance  = [{'url': appearance}]
            if not isinstance(appearance, list):
                appearance = [appearance]
            # get also the firstAppearance
            firstAppearance = itemReviewed.get('firstAppearance', None)
            if not isinstance(firstAppearance, list):
                firstAppearance = [firstAppearance]
            appearances = firstAppearance + appearance
            if appearances:
                # new field appearance in https://pending.schema.org/Claim
                #print(appearances)
                result.extend([el['url'] for el in appearances if el])
            # sometimes instead the appearances are listed in itemReviewed
            sameAs = itemReviewed.get('sameAs', None)
            if sameAs:
                result.append(sameAs)
            else:
                author = itemReviewed.get('author', None)
                if not author:
                    author = itemReviewed.get('properties', {}).get('author', None)
                if author:
                    sameAs = author.get('sameAs', None)
                    if not sameAs:
                        sameAs = author.get('properties', {}).get('sameAs', None)
                if sameAs:
                    if isinstance(sameAs, list):
                        result.extend(sameAs)
                    else:
                        result.append(sameAs)
            # sometimes in itemReviewed.url
            itemReviewed_url = itemReviewed.get('url', None)
            if itemReviewed_url:
                #raise ValueError(claimreview['url'])
                result.append(itemReviewed_url)
        # TODO also return sameAs if present on the claim directly, other links there!!

        # split appearances that are a single field with comma or ` and `
        cleaned_result = []
        for el in result:
            if not isinstance(el, str):
                cleaned_result.extend(el)
            if ',' in el:
                els = el.split(',')
                cleaned_result.extend(els)
            if ' ' in el:
                els = el.split(' ')
                cleaned_result.extend(els)
            elif ' and ' in el:
                els = el.split(' and ')
                cleaned_result.extend(els)
            else:
                cleaned_result.append(el)
        # remove spaces around
        cleaned_result = [el.strip() for el in cleaned_result if el]
        # just keep http(s) links
        cleaned_result = [el for el in cleaned_result if re.match('^https?:\/\/.*$', el)]
        # remove loops to evaluation of itself
        cleaned_result = [el for el in cleaned_result if utils.get_url_domain(el) != factchecker_domain]
        return cleaned_result
    except Exception as e:
        print(claimreview)
        raise(e)


def extract():
    """Filtering function that analyses ClaimReviews and extracts tweet ratings."""

    ifcn_domains = get_ifcn_domains()


    filtered_cr = []
    tweet_reviews = defaultdict(list) # id: {label (mapped), original_label, id, fulltext}
    not_ifcn_cnt = 0
    not_ifcn_review_domains = set()
    not_twitter_cnt = 0
    errror_tweet_id_cnt = 0
    errror_twitter_api_cnt = 0
    multiple_reviews_cnt = 0
    disagreeing_cnt = 0
    disagreeing_reviews = {}
    for cr in client['claimreview_scraper']['claim_reviews'].find():
        try:
            url = cr.get('url', '')
            domain = utils.get_url_domain(url)
            appearances = claimreview_get_claim_appearances(cr)
            if domain not in ifcn_domains:
                not_ifcn_cnt += 1
                not_ifcn_review_domains.add(domain)
                # raise ValueError(3)
                continue
            twitter_match = False
            review_rating = cr.get('reviewRating', {})
            original_label = review_rating.get('alternateName', '')
            mapped_label = claimreview_get_coinform_label(cr)
            for a in appearances:
                try:
                    match = re.search(r'https://twitter\.com/[A-Za-z0-9_]+/status/(?P<tweet_id>[0-9]+).*', a)
                    tweet_id = match.group('tweet_id')
                    tweet_id = int(tweet_id)
                # a_domain = utils.get_url_domain(a)
                # if a_domain == 'twitter.com':
                #     try:
                #         if a.endswith('/'):
                #             a = a[:-1]
                #         tweet_id = int(a.split('/')[-1].split('?')[0])
                except Exception:
                    print('not with a tweet id', a)
                    errror_tweet_id_cnt += 1
                    continue
                    
                filtered_cr.append(cr)
                tweet_reviews[tweet_id].append({
                    'label': mapped_label,
                    'original_label': original_label,
                    'review_rating': review_rating,
                    'claim_reviewed': cr['claimReviewed'],
                    'review_url': cr['url'],
                    'retrieved_by': cr['retrieved_by']
                })
                twitter_match = True
            if not twitter_match:
                not_twitter_cnt += 1
        except Exception as e:
            print(e)
            raise ValueError(cr)


    write_json_with_path(list(not_ifcn_review_domains), data_path, 'not_ifcn_sources.json')

    results = []
    for tweet_id, reviews in tqdm.tqdm(tweet_reviews.items(), desc='second loop'):
        if len(reviews) > 1:
            multiple_reviews_cnt += 1
        
        # check that the ratings agree
        labels = set(el['label'] for el in reviews)
        if len(labels) > 1:
            disagreeing_cnt += 1
            label = 'check_me'
            disagreeing_reviews[tweet_id] = reviews
        else:
            label = labels.pop()

        try:
            res = requests.get(f'{TWITTER_CONNECTOR}/tweets/{tweet_id}')
            res.raise_for_status()
            t = res.json()
            text = t['text']
            created_at = t['created_at']
            lang = t['lang']
            screen_name = t['user_screen_name']
        except Exception as e:
            print('API error', e, tweet_id)
            errror_twitter_api_cnt += 1
            text = None
            created_at = None
            lang = None
            screen_name = None

        results.append({
            'id': tweet_id,
            'label': label,
            'full_text': text,
            'created_at': created_at,
            'screen_name': screen_name,
            'lang': lang,
            'reviews': reviews
        })
        

    write_json_with_path(disagreeing_reviews, data_path, 'tweet_disagreeing_reviews.json')
    
    print('not ifcn', not_ifcn_cnt)
    print('not twitter', not_twitter_cnt)
    print('error tweet id', errror_tweet_id_cnt)
    print('error twitter API', errror_twitter_api_cnt)
    print('multiple reviews', multiple_reviews_cnt)
    print('multiple reviews disagreeing', disagreeing_cnt)

    print('there are', len(results), 'tweet reviews')

    write_json_with_path(tweet_reviews, data_path, 'tweet_reviews.json')
    # analyse_mapping()

    return {
        'tweet_reviews_count': len(results),
        'not_twitter_count': not_twitter_cnt,
        'error_tweet_id_count': errror_tweet_id_cnt,
        'error_twitter_api_count': errror_twitter_api_cnt,
        'tweets_with_multiple_reviews_count': multiple_reviews_cnt,
        'tweets_with_disagreeing_reviews_count': disagreeing_cnt
    }

def analyse_mapping():
    """see what got mapped to what"""
    reviews = read_json(data_path / 'tweet_reviews.json')
    m = defaultdict(set)
    for r in reviews:
        # TODO error here TypeError: string indices must be integers
        for el in r['reviews']:
            m[el['label']].add(el['original_label'])
    
    for k, v in m.items():
        m[k] = list(v)
    write_json_with_path(m, data_path, 'mapping.json')




def filter_data():
    import pandas as pd
    import dateparser
    data = read_json(data_path / 'tweet_reviews.json')
    start_date = dateparser.parse('1 september 2020')

    for d in data:
        del d['reviews']

    df = pd.DataFrame(data)
    parsing_fn = lambda v: dateparser.parse(v.replace('+0000', '')) if v else None
    tweet_url_fn = lambda v: f'https://twitter.com/{v["screen_name"]}/status/{v["id"]}' if v["screen_name"] else None
    df['created_at_parsed'] = df['created_at'].apply(parsing_fn)
    df['tweet_url'] = df.apply(tweet_url_fn, axis=1)

    df_recent = df[df['created_at_parsed'] >= start_date]
    by_label = df_recent.groupby('label').count()
    df_recent_credible = df_recent[df_recent['label'] == 'credible']
    df_recent_mostly_credible = df_recent[df_recent['label'] == 'mostly_credible']
    df_recent_ok = pd.concat([df_recent_credible, df_recent_mostly_credible])
    df_recent_ok.to_csv('data/tweet_reviews_credible_or_mostly_september_october.tsv', sep='\t', index=False)

    df_credible = df[df['label'] == 'credible']
    df_mostly_credible = df[df['label'] == 'mostly_credible']
    df_ok = pd.concat([df_credible, df_credible])
    df_ok.to_csv('data/tweet_reviews_credible_or_mostly.tsv', sep='\t', index=False)
    df_ok_en = df_ok[df_ok['lang'] == 'en']
    df_ok_en.to_csv('data/tweet_reviews_credible_or_mostly_english.tsv', sep='\t', index=False)

if __name__ == "__main__":
    extract()
