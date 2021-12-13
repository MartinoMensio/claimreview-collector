# additional requirements: 
# plotly 
# streamlit

import streamlit as st

import re
import json
import flatten_json
import pandas as pd
from tqdm import tqdm
from collections import defaultdict
from goose3 import Goose
import csv

import plotly.express as px
import plotly.graph_objects as go


from claimreview_scraper.processing import utils, cache_manager

claims_path = 'data/latest/claim_reviews.json'


# @st.cache
@st.spinner(text='loading raw data')
def read_json(path):
    with open(path) as f:
        result = json.load(f)
    return result

def write_json(path, content):
    with open(path, 'w') as f:
        json.dump(content, f, indent=2)

st.title('ClaimReview appearances analyisis')
crs = read_json(claims_path)

cr_by_url = {el['review_url'] for el in crs}

st.text(f'There are {len(crs)} claimReviews, appearing on {len(cr_by_url)} different urls')


# all the appearance urls by domain
appearances = []
for cr in tqdm(crs, desc='analysing appearances'):
    for appearance_url in cr['appearances']:
        appearance_domain = utils.get_url_domain(appearance_url)
        review_domain = utils.get_url_domain(cr['review_url'])
        appearances.append({
            'url': appearance_url,
            'domain': appearance_domain,
            'label': cr['label'],
            'original_label': cr['reviews'][0]['original_label'],
            'review_url': cr['review_url'],
            'review_domain': review_domain,
        })
df = pd.DataFrame(appearances)
by_domain = df.groupby(['domain', 'label']).count().sort_values('url',ascending=False)
# by_domain = df.groupby('domain').count()['url'].sort_values( ascending=False)
st.write(by_domain)
by_domain.head(100)
fig = go.Figure(data=[go.Histogram(x=df['domain'])])
fig.update_xaxes(categoryorder='total descending')
st.plotly_chart(fig)


goose = Goose()
for el in tqdm(appearances):
    if el['domain'] in ['facebook.com', 'twitter.com', 'youtube.com', 'instagram.com', 'youtu.be']:
        continue
    try:
        page_text = cache_manager.get(el['url'], verify=False)
        article = goose.extract(raw_html=page_text)
        el['goose'] = article.infos
    except Exception as e:
        print(e)
        continue

len([el for el in appearances if 'goose' in el])
appearances = [el for el in appearances if 'goose' in el]

write_json('data/latest/appearances_with_content.json', appearances)
raise ValueError('stop')

by_appearance_url_domains = defaultdict(set)
by_appearance_url = defaultdict(dict)
for el in appearances:
    by_appearance_url_domains[el['url']].add(el['review_domain'])
    by_appearance_url[el['url']][el['review_domain']] = el
# with more than 2 reviews
with_multiple = {k: v for k, v in by_appearance_url_domains.items() if len(v) > 1}
with_multiple_table = []
fieldnames = ['url']
for url, domains in with_multiple.items():
    row = {'url': url}
    for i, domain in enumerate(domains):
        row[f'review_domain_{i}'] = domain
        row[f'review_url_{i}'] = by_appearance_url[url][domain]['review_url']
        row[f'label_{i}'] = by_appearance_url[url][domain]['label']
        row[f'original_label_{i}'] = by_appearance_url[url][domain]['original_label']
        if f'review_domain_{i}' not in fieldnames:
            fieldnames.extend([f'review_domain_{i}', f'review_url_{i}', f'label_{i}', f'original_label_{i}'])
    with_multiple_table.append(row)
with open('data/latest/appearances_with_multiple_reviews.tsv', 'w') as f:
    writer = csv.DictWriter(f, delimiter='\t', fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(with_multiple_table)


# let's see which properties are used
by_json_property = defaultdict(int)
for cr in tqdm(crs):
    flatten_cr = flatten_json.flatten(cr, separator='.')
    for k,v in flatten_cr.items():
        if k.startswith('ifcn_info'):
            continue
        k_clean = re.sub(r'\.\d+', '', k)
        by_json_property[k_clean] += 1

# st.bar_chart(list(by_json_property.items()))
# ks, vs = list(by_json_property.keys()), list(by_json_property.values())
ks = []
vs = []
for k,v in by_json_property.items():
    if 'url' in k or 'appearance' in k or 'sameAs' in k:
        ks.append(k)
        vs.append(v)

fig = go.Figure(go.Bar(x=ks, y=vs))
# fig.update_yaxes(type='category')
# fig.show()
st.plotly_chart(fig)



# time of fact-check
misinforming_urls_path = 'data/latest/links_not_credible_full.json'
data = read_json(misinforming_urls_path)
for el in data:
    el['date_published'] = max(r['date_published'] for r in el['reviews'])
df = pd.DataFrame(data)

fig = go.Figure(data=[go.Histogram(x=df['date_published'])])
# fig.show()
st.plotly_chart(fig)

