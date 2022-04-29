import os
import json
import requests
import pandas as pd
from tqdm import tqdm
from multiprocessing.pool import ThreadPool
import plotly.express as px
from pathlib import Path


import claimreview_scraper
from claimreview_scraper.processing import database_builder, utils
from claimreview_scraper.processing import claimreview
from claimreview_scraper.routers import data


# STEPS:
# - get all ClaimReviews as before
# - collect them again (cache) from the fact-checking website (to remove Google Factcheck Tools mismatches)
# - process as before ()



# BEFORE cleaning
# "claim_reviews": {
#       "claimreviews_merged_count": 126248,
#       "raw_claimreviews_count": 203257,
#       "ifcn_domains_count": 117,
#       "claimreviews_not_from_ifcn_count": 34551,
#       "claimreviews_unique_review_urls_count": 110008,
#       "claimreviews_unique_appearances_count": 59443,
#       "not_matching_reviews_labels_count": 1035,
#       "links_not_credible_count": 51262
#     },

# TODO from raw
# claimreviews = utils.read_json('data/latest/claim_reviews_raw.json')
# claimreviews = database_builder.get_all_factchecking_urls()
# urls = list(set(el['url'] for el in claimreviews))
# original = []
# with ThreadPool(8) as pool:
#     for url, crs in tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls_100), total=len(urls_100)):
#         original.extend(crs)

# TODO only from links not credible table
links = utils.read_json('data/latest/links_all_full.json')

# check satisfy condition
links = [el for el in links if data.check_satisfy(el)]

for el in links:
    date = max((r['date_published'] for r in el['reviews'] if r['date_published']), default='0')
    el['date_published'] = date

# sort by most recent
sorted_links = sorted(links, key=lambda row: row['date_published'], reverse=True)

languages_map = {}
languages_cache_path = 'languages_cache.json'
if os.path.exists(languages_cache_path):
    languages_map = utils.read_json(languages_cache_path)
def get_language(text):
    if text in languages_map:
        return languages_map[text]
    else:
        res = requests.post('https://api.textrazor.com/', headers={'X-TextRazor-Key': '113a014b5a98b3eab42fb073646cdac079d232fe2f28eef001190ce1'}, data={
            'text': text,
        })
        if res.status_code != 200:
            print(res.text)
            error = res.json()['error']
            if 'TextRazor cannot analyze documents of language: ':
                language = error.split('TextRazor cannot analyze documents of language: ')[1][:3]
            else:
                raise ValueError(error)
        else:
            language = res.json()['response']['language']
        languages_map[text] = language
        return language


table = [{
    'misinforming_url': row['misinforming_url'],
    'misinforming_domain': row['misinforming_domain'],
    'date_published': row['date_published'],
    'n_reviews': len(row['reviews']),
    'review_url': row['reviews'][0]['review_url'],
    'label': row['reviews'][0]['label'],
    'original_label': row['reviews'][0]['original_label'],
    'fact_checker': row['reviews'][0]['fact_checker']['name'],
    'country': row['reviews'][0]['fact_checker']['country'],
    'claim_text': row['reviews'][0]['claim_text'][0].replace('\n', '\\n'),
} for row in sorted_links]

urls = list(set(el['review_url'] for el in table))


# ukraine filter
keyword_list = ['ukraine', 'ucraina', 'ucrania']
with_ukraine = [el for el in table if any(keyword in ' '.join([el['claim_text'],el['review_url']]).lower() for keyword in keyword_list)]

date_start = '2021-11-01'
with_ukraine_recent = [el for el in with_ukraine if el['date_published'] > date_start]

for el in tqdm(with_ukraine_recent, desc='getting language'):
    el['factcheck_language'] = get_language(el['claim_text'])

utils.write_json_with_path(languages_map, Path(''), 'languages_cache.json')

df = pd.DataFrame(with_ukraine_recent)
# date filter
df = df[df['date_published'] > date_start]



fig = px.histogram(df, x="date_published")
fig.show()
fig = px.histogram(df, x="label")
fig.show()
fig = px.histogram(df, x="fact_checker")
fig.show()
fig = px.histogram(df, x="factcheck_language")
fig.show()
fig = px.histogram(df, x="misinforming_domain")
fig.show()

df.to_csv('ukraine.tsv', sep='\t', index=False)
# df.to_csv('cleaned_table_recollected.csv', sep='\t', index=False)
raise ValueError(1234)

by_factchecker_100 = df.groupby('fact_checker').head(100).reset_index(drop=True).sort_values(['fact_checker', 'date_published'], ascending=[True, False])
by_factchecker_100.to_csv('by_factchecker_100.csv', sep='\t', index=False)


### plot
from claimreview_scraper.processing import utils
from plotly import graph_objects as go
import pandas as pd
index = utils.read_json('data/index.json')
latest = index['latest']
comparison = latest['claim_reviews']['recollection_stats']
domains, before, after = zip(*[(el['domain'], el['before'], el['after']) for el in comparison])

fig = go.Figure([
    go.Bar(y=domains, x=before, orientation='h', name='before'),
    go.Bar(y=domains, x=after, orientation='h', name='recollected'),
    ])
fig.update_yaxes(dtick=1)
fig.update_layout(height=2000)
fig.show()
fig.write_image('data/latest/recollection_stats.pdf')
fig.write_image('data/latest/recollection_stats.png')

# then provide some samples for each fact-checker
# see above