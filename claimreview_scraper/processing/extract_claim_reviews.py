import os
import json
import tqdm
import scipy
import requests
import jellyfish
import dateparser
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage
from collections import defaultdict
from pathlib import Path
from multiprocessing.pool import ThreadPool

from . import utils
from . import extract_tweet_reviews, database_builder
from . import claimreview


client = database_builder.client
data_path = Path('data/latest')


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

    ifcn_signatories = utils.read_json(data_path /'ifcn_sources.json')

    countries_cnt = defaultdict(int)
    for sig in ifcn_signatories:
        domain = sig['domain']
        country = sig['original']['country']
        countries_cnt[country] += len(urls_by_domain[domain])
    utils.write_json_with_path(countries_cnt, data_path, 'fact_checks_by_country.json')

    
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


def extract_ifcn_claimreviews(domains=None, recollect=True):
    if domains:
        ifcn_domains = {k: {
            'original': {'name': k,
                'country': k,
                'language': k,
                'website': k,
                'ifcn_url': k,
                'assessment_url': k,
                'avatar': k
            },
            'domain': k
        } for k in domains}
    else:
        ifcn_domains = extract_tweet_reviews.get_ifcn_domains()
    not_ifcn_cnt = 0
    not_ifcn_urls = set()
    not_ifcn_review_domains = set()

    
    urls_to_recollect = set()
    urls_to_recollect_by_factchecker = defaultdict(set)
    raw_crs = []
    raw_crs_filtered = []
    # step 1: determine which claim reviews to recollect from fact-checker
    for cr in client['claimreview_scraper']['claim_reviews'].find():
        del cr['_id']
        raw_crs.append(cr)
        url = cr.get('url', '')
        domain = utils.get_url_domain(url)
        if domain not in ifcn_domains:
            not_ifcn_urls.add(url)
            not_ifcn_cnt += 1
            not_ifcn_review_domains.add(domain)
        else:
            urls_to_recollect.add(url)
            urls_to_recollect_by_factchecker[domain].add(url)
            raw_crs_filtered.append(cr)
    
    utils.write_json_with_path(raw_crs, data_path, 'claim_reviews_raw.json')

    print('raw_crs', len(raw_crs))
    print('urls_to_recollect', len(urls_to_recollect))

    if recollect:
        # step 2: recollect from fact-checker
        # recollected_crs = utils.read_json(data_path / 'claim_reviews_raw_recollected.json')
        recollected_crs = []
        with ThreadPool(8) as pool:
            for url, crs in tqdm.tqdm(pool.imap_unordered(claimreview.retrieve_claimreview, urls_to_recollect), total=len(urls_to_recollect), desc='recollecting'):
                recollected_crs.extend(crs)
        utils.write_json_with_path(recollected_crs, data_path, 'claim_reviews_raw_recollected.json')

        # step 3: observe what has been lost
        print('recollected_crs', len(recollected_crs))
        recollected_crs_urls = set(el.get('url', '') for el in recollected_crs)
        # observe by fact-checker
        recollected_crs_urls_by_factchecker = defaultdict(set)
        for url in recollected_crs_urls:
            domain = utils.get_url_domain(url)
            recollected_crs_urls_by_factchecker[domain].add(url)
        comparison_recollection = []
        for domain in ifcn_domains:
            before_len = len(urls_to_recollect_by_factchecker[domain])
            if before_len:
                comparison_recollection.append({
                    'domain': domain,
                    'before': before_len,
                    'after': len(recollected_crs_urls_by_factchecker[domain])
                })
    else:
        recollected_crs = raw_crs_filtered
        comparison_recollection = []

    cr_by_url = defaultdict(list)

    for cr in recollected_crs:
        # del cr['_id']
        raw_crs.append(cr)
        url = cr.get('url', '')
        domain = utils.get_url_domain(url)
        cr['ifcn_info'] = ifcn_domains[domain]
        cr_by_url[url].append(cr)

    results = []
    different_texts = {}
    # check which ones are duplicated
    for url, crs in tqdm.tqdm(cr_by_url.items(), desc='extracting reviews'):
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
                date_published = cr.get('datePublished', None)
                if date_published:
                    date_published = dateparser.parse(date_published)
                if date_published:
                    date_published = date_published.strftime("%Y-%m-%d")
                cr['date_published'] = date_published
            # claimreviews have the same text claim checked, they must have same verdict
            if len(labels) > 1:
                # print(claims_reviewed)
                # print(labels)
                # print([el['retrieved_by'] for el in crs_cluster])
                final_label = 'check_me'
            else:
                final_label = labels.pop()

            # the same in the same cluster, because same URL gives same domain
            factchecker_info = crs_cluster[0]['ifcn_info']
            
            results.append({
                'claim_text': cluster_claims_reviewed,
                'label': final_label,
                'review_url': url,
                'fact_checker': {
                    'name': factchecker_info['original']['name'],
                    'country': factchecker_info['original']['country'],
                    'language': factchecker_info['original']['language'],
                    'website': factchecker_info['original']['website'],
                    'ifcn_url': factchecker_info['original']['assessment_url'],
                    'avatar': factchecker_info['original']['avatar'],
                    'domain': factchecker_info['domain']
                },
                'appearances': list(appearances),
                'reviews': [{
                    'label': extract_tweet_reviews.claimreview_get_coinform_label(cr),
                    'original_label': cr.get('reviewRating', {}).get('alternateName', ''),
                    'review_rating': cr.get('reviewRating', {}),
                    'retrieved_by': cr.get('retrieved_by', None),
                    'date_published': cr['date_published']
                } for cr in crs_cluster]
            })



    print('not_ifcn_domains', not_ifcn_review_domains)
    print('not_ifcn_cnt', not_ifcn_cnt)
    print('len cr_by_url', len(cr_by_url))
    print('len results', len(results))

    utils.write_json_with_path(list(not_ifcn_review_domains), data_path, 'not_ifcn_sources.json')

    utils.write_json_with_path(results, data_path, 'claim_reviews.json')
    # 10190
    utils.write_json_with_path({k: list(v) for k, v in different_texts.items()}, data_path, 'different_texts.json')

    appearances = set()
    for cr in results:
        appearances.update(cr['appearances'])
    check_me = [cr for cr in results if cr['label'] == 'check_me']
    check_me_count = len(check_me)
    by_url = defaultdict(list)
    for cr in results:
        for appearance in cr['appearances']:
            by_url[appearance].append(cr)
    disagreeing_reviews = {}
    for url, reviews in by_url.items():
        labels = set(el['label'] for el in reviews)
        if len(labels) > 1:
            disagreeing_reviews[url] = reviews
    utils.write_json_with_path(disagreeing_reviews, data_path, 'disagreeing_reviews.json')

    # not credible links only
    bad_links = set()
    for cr in results:
        if cr['label'] == 'not_credible':
            bad_links.update(cr['appearances'])
    bad_links = list(bad_links)
    utils.write_json_with_path(bad_links, data_path, 'links_not_credible.json')

    # not credible links table
    by_bad_link = defaultdict(list)
    for cr in results:
        if cr['label'] == 'not_credible':
            for app in cr['appearances']:
                by_bad_link[app].append(cr)
    
    # multiple reviews but agreeing
    multiple = 0
    for k, v in by_bad_link.items():
        if len(v) > 1:
            # print(k, v)
            multiple += 1
    print('urls with multiple (not credible)', multiple)

    # linked information result
    bad_table = []
    for k, v in by_bad_link.items():
        bad_table.append({
            'misinforming_url': k,
            'misinforming_domain': utils.get_url_domain(k),
            'reviews': [{
                'label': r['label'],
                'review_url': r['review_url'],
                'claim_text': r['claim_text'],
                'fact_checker': r['fact_checker'],
                # using element [0] because they already have the same fact-check URL, same claim reviewed, same mapped label
                'original_label': r['reviews'][0]['original_label'],
                'date_published': r['reviews'][0]['date_published'],
            } for r in v]
        })
    utils.write_json_with_path(bad_table, data_path, 'links_not_credible_full.json')


    # all the links
    links = set()
    for cr in results:
        links.update(cr['appearances'])
    links = list(links)
    utils.write_json_with_path(links, data_path, 'links_all.json')

    # not credible links table
    by_link = defaultdict(list)
    for cr in results:
        for app in cr['appearances']:
            by_link[app].append(cr)
    
    # multiple reviews but agreeing
    multiple = 0
    for k, v in by_link.items():
        if len(v) > 1:
            # print(k, v)
            multiple += 1
    print('urls with multiple', multiple)

    # linked information result
    table = []
    for k, v in by_link.items():
        table.append({
            'misinforming_url': k,
            'misinforming_domain': utils.get_url_domain(k),
            'reviews': [{
                'label': r['label'],
                'review_url': r['review_url'],
                'claim_text': r['claim_text'],
                'fact_checker': r['fact_checker'],
                # using element [0] because they already have the same fact-check URL, same claim reviewed, same mapped label
                'original_label': r['reviews'][0]['original_label'],
                'date_published': r['reviews'][0]['date_published'],
            } for r in v]
        })
    utils.write_json_with_path(table, data_path, 'links_all_full.json')



    return {
        'raw_claimreviews_count': len(raw_crs),
        'raw_claimreviews_recollected_count': len(recollected_crs),
        'recollection_stats': comparison_recollection,
        'claimreviews_merged_count': len(results),
        'ifcn_domains_count': len(ifcn_domains),
        'claimreviews_not_from_ifcn_count': len(not_ifcn_urls),
        'claimreviews_unique_review_urls_count': len(cr_by_url),
        'claimreviews_unique_appearances_count': len(appearances),
        'not_matching_reviews_labels_count': check_me_count,
        'links_not_credible_count': len(bad_links),
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


def analyse_mapping():
    """see what got mapped to what"""
    reviews = utils.read_json(data_path / 'claim_reviews.json')
    m = defaultdict(lambda: defaultdict(int))
    domains_by_label = defaultdict(set)
    for r in reviews:
        for el in r['reviews']:
            m[el['label']][el['original_label']] += 1
            domains_by_label[el['original_label']].add(r['fact_checker']['domain'])
    # for k, v in m.items():
    #     m[k] = list(v)
    stats = []
    for coinform_label, values in m.items():
        for original_label, counts in values.items():
            stats.append({
                'original_label': original_label,
                'coinform_label': coinform_label,
                'domains': ','.join(domains_by_label[original_label]),
                'count': counts,
            })
    utils.write_json_with_path(stats, data_path, 'claim_labels_mapping.json')

    rows = sorted(stats, key=lambda el: el['count'], reverse=True)
    df = pd.DataFrame(rows)
    df.to_csv(data_path/'labels.tsv', index=False, sep='\t')
    print(df.groupby('coinform_label').sum())







def main():
    # claims_nationality_distribution()
    extract_ifcn_claimreviews()


if __name__ == "__main__":
    main()