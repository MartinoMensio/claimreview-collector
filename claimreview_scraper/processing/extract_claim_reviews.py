import os
import json
import tqdm
import scipy
import requests
import jellyfish
import numpy as np
from scipy.cluster.hierarchy import linkage
from collections import defaultdict
from pathlib import Path

from . import utils
from . import extract_tweet_reviews, database_builder


client = database_builder.client
data_path = Path('data/latest')

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





def claims_nationality_distribution():
    ifcn_domains = extract_tweet_reviews.get_ifcn_domains()
    urls = set(client['claimreview_scraper']['claim_reviews'].distinct('url'))
    print(len(urls), 'unique fact-checking URLs')
    urls_by_domain = defaultdict(list)
    # filter published by IFCN signatories
    domain_ifcn_cnt = 0
    for el in urls:
        domain = utils.get_url_domain(el)
        urls_by_domain[domain].append(el)
        if domain in ifcn_domains:
            domain_ifcn_cnt += 1
    print(domain_ifcn_cnt, 'published by IFCN signatories')

    ifcn_signatories = read_json(data_path /'ifcn_sources.json')

    countries_cnt = defaultdict(int)
    for sig in ifcn_signatories:
        domain = sig['domain']
        country = sig['original']['country']
        countries_cnt[country] += len(urls_by_domain[domain])
    write_json_with_path(countries_cnt, data_path, 'fact_checks_by_country.json')

    
    # create nice plot (requires plotly installed)
    if False:
        import pandas as pd
        import plotly.express as px
        t = [{'country': k, 'count': v} for k,v in countries_cnt.items()]
        t = sorted(t, key=lambda el: el['count'], reverse=True)
        df = pd.DataFrame(t)
        fig = px.bar(df, x='country', y='count')
        fig.show()
        fig.write_image("countries_factchecks_counts.pdf")


def extract_ifcn_claimreviews():
    ifcn_domains = extract_tweet_reviews.get_ifcn_domains()
    not_ifcn_urls = set()
    not_ifcn_cnt = 0
    not_ifcn_review_domains = set()
    cr_by_url = defaultdict(list)
    raw_crs = []
    for cr in client['claimreview_scraper']['claim_reviews'].find():#.limit(100000):
        del cr['_id']
        raw_crs.append(cr)
        url = cr.get('url', '')
        domain = utils.get_url_domain(url)
        if domain not in ifcn_domains:
            not_ifcn_urls.add(url)
            not_ifcn_cnt += 1
            not_ifcn_review_domains.add(domain)
        else:
            cr_by_url[url].append(cr)

    write_json_with_path(raw_crs, data_path, 'claim_reviews_raw.json')

    results = []
    different_texts = {}
    # check which ones are duplicated
    for url, crs in tqdm.tqdm(cr_by_url.items()):
        try:
            # one text for each ClaimReview
            claims_reviewed = []
            for el in crs:
                claim_reviewed = el.get('claimReviewed', '')
                if isinstance(claim_reviewed, list):
                    claim_reviewed = claim_reviewed[0]
                claim_reviewed = claim_reviewed.strip()
                claims_reviewed.append(claim_reviewed)
        except:
            print(crs)
            raise ValueError(url)

        

        # there can be more than one claimreview at this url
        # merging almost identical strings (low levenshtein distances: allow 5 characters to differ)
        # print(claims_reviewed)
        if len(crs) > 1:
            indexes = cluster_sentences(claims_reviewed, max_distance=5)
        else:
            indexes = [[0]]

        if len(indexes) > 1:
            different_texts[url] = []
            multiple = True
        else:
            multiple = False
        for c, cluster_indexes in enumerate(indexes):
            # only the selected indexes
            # print(cluster_indexes)
            # print(len(crs))
            crs_cluster = [crs[i] for i in cluster_indexes]
            cluster_claims_reviewed = [claims_reviewed[i] for i in cluster_indexes]
            cluster_claims_reviewed = list(set(cluster_claims_reviewed))
            if multiple:
                different_texts[url].append(cluster_claims_reviewed)

            labels = set()
            appearances = set()
            for cr in crs_cluster:
                mapped_label = extract_tweet_reviews.claimreview_get_coinform_label(cr)
                labels.add(mapped_label)
                appearances.update(extract_tweet_reviews.claimreview_get_claim_appearances(cr))
            # claimreviews have the same text claim checked, they must have same verdict
            if len(labels) > 1:
                # print(claims_reviewed)
                # print(labels)
                # print([el['retrieved_by'] for el in crs_cluster])
                final_label = 'check_me'
            else:
                final_label = labels.pop()
            
            results.append({
                'claim_text': cluster_claims_reviewed,
                'label': final_label,
                'review_url': url,
                'appearances': list(appearances),
                'reviews': [{
                    'label': extract_tweet_reviews.claimreview_get_coinform_label(cr),
                    'original_label': cr.get('reviewRating', {}).get('alternateName', ''),
                    'review_rating': cr.get('reviewRating', {}),
                    'retrieved_by': cr['retrieved_by']
                } for cr in crs_cluster]
            })



    print('not_ifcn_domains', not_ifcn_review_domains)
    print('not_ifcn_cnt', not_ifcn_cnt)
    print('len cr_by_url', len(cr_by_url))
    print('len results', len(results))

    write_json_with_path(list(not_ifcn_review_domains), data_path, 'not_ifcn_sources.json')

    write_json_with_path(results, data_path, 'claim_reviews.json')
    # 10190
    write_json_with_path({k: list(v) for k, v in different_texts.items()}, data_path, 'different_texts.json')

    appearances = set()
    for cr in results:
        appearances.update(cr['appearances'])
    check_me_count = len([cr for cr in results if cr['label'] == 'check_me'])

    # bad links only
    bad_links = set()
    for cr in results:
        if cr['label'] == 'not_credible':
            bad_links.update(cr['appearances'])
    bad_links = list(bad_links)
    write_json_with_path(bad_links, data_path, 'links_not_credible.json')

    return {
        'claimreviews_merged_count': len(results),
        'raw_claimreviews_count': len(raw_crs),
        'ifcn_domains_count': len(ifcn_domains),
        'claimreviews_not_from_ifcn_count': len(not_ifcn_urls),
        'claimreviews_unique_review_urls_count': len(cr_by_url),
        'claimreviews_unique_appearances_count': len(appearances),
        'not_matching_reviews_labels_count': check_me_count,
        'links_not_credible_count': len(bad_links)
    }





def cluster_sentences(sentences, max_distance=3):
    tri_len = int(scipy.special.binom(len(sentences), 2))
    reduced_sentence_matrix = np.zeros((tri_len))
    cnt = 0
    for i in range(len(sentences) - 1):
        sent_i = sentences[i]
        for j in range(i + 1, len(sentences)):
            sent_j = sentences[j]
            lev = jellyfish.levenshtein_distance(sent_i, sent_j)
            reduced_sentence_matrix[cnt] = lev
            cnt += 1
    Z = linkage(reduced_sentence_matrix, 'ward', 'euclidean')

    # maximum distance
    distance_inter = max_distance

    # indexes
    filtered_clusters = [[el] for el in range(len(sentences))] + [[]] * (len(sentences) -1)
    for i, step in enumerate(Z):
        if step[2] > distance_inter:
            break
        # remove from previous cluster
        a_index = int(step[0])
        b_index = int(step[1])
        # add to the current cluster
        a = filtered_clusters[a_index]
        b = filtered_clusters[b_index]
        new_index = i + len(sentences)
        filtered_clusters[new_index] = a + b
        filtered_clusters[a_index] = []
        filtered_clusters[b_index] = []

    # filter the empty
    filtered_clusters = [el for el in filtered_clusters if len(el) > 0]

    # if len(filtered_clusters) > 1:
    #     print(sentences)
    #     print(filtered_clusters)
    #     exit(1)

    return filtered_clusters








def main():
    # claims_nationality_distribution()
    extract_ifcn_claimreviews()


if __name__ == "__main__":
    main()