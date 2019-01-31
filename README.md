
# Datasets

This folder contains the different datasets that we collected.

The goal is to acquire as many as possible urls with a label that tells if they are true or fake.

For this purpose we use a binary lable (true or fake).

We select from the datasets only items that are (almost) completely true or fake, removing the variations in the middle.

Goal: have a list of URL labelled with `fake` / `true`

## Types of data

### fact_checking_url

It is a flat object that contains fields from claimReview

```jsonc
{
    "url": "url", // the url to the fact checking article. Same as claimReview.url. Required
    "source": "dataset_name", // where this record comes from. Required. Can also be an array
    "title": "title of fact checking article", // when is already known from the dataset
    "subtitle": "subtitle or description", // when is already known from the dataset
    "claim": "the reviewed textual claim", // when is already known from the dataset
    "claim_url": "the url to the claim",
    "label": "textual label", // when the label is already known from the dataset
    "original_label": "textual label", // not simplified to 'true'/'fake'
    "reason": "textual reason", // when is already known from the dataset
    "date": "date in isoformat", // when is already known from the dataset
    "author": "name of the author", // when is already known from the dataset
}
```

### ClaimReview

Only the relevant fields are listed

```jsonc
{
    "url": "url", // the url where this ClaimReview belongs, is the fact checking article
    "claimReviewed": "text", // the specific textual claim that is being reviewed
    "itemReviewed": {
        "url": "url", // when available, put here the url of the claim (can come from the author, ...)
    },
    "reviewRating": {
        "ratingValue": -1, // when available, the current value that belongs to the [worstValue, bestValue] interval
        "worstValue": -1, // inferior bound for ratingValue
        "bestValue": -1, // superior bound for ratingValue
        "alternateName": "textual label" // to be used as label, especially when the ratingValue is not available
    },
    "author": {
    }
}
```

## From one type of data to the other

```text
ClaimReview
    fact_checking_url
fact_checking_url
    if claim_url: url_label(claim_url)
    url_label(url)
fact_checking_url
    if claim_url: claim
fact_checking_url
    Rebuttal(claim_url, url)
TextualClaim
    ClaimReview (use google_factcheck_explorer search)
```

## `google_factcheck_explorer`

Type: aggregator of ClaimReview items

url: https://toolbox.google.com/factcheck/explorer

size: ~28000 items

used for: ClaimReviews, fact_checking_urls

Requires env variable `GOOGLE_FACTCHECK_EXPLORER_COOKIE` in the `.env` file. Just inspect from your browser and copy it.

## `datacommons_factcheck`

type: aggregator of ClaimReview items

url: https://www.datacommons.org/factcheck/download

size: 10564 items

used for: ClaimReviews, fact_checking_urls

## `datacommons_feeds`

type: aggregator of ClaimReview items

url: https://storage.googleapis.com/datacommons-feeds/claimreview/latest/data.json

size: 43 items

used for: ClaimReviews, fact_checking_urls

## `mrisdal_fakenews`

type: articles (title, text, author, date, language, site_url, country, domain_rank, spam_score, facebook_likes&comments&shares) + labels coming from bs_detector

url: https://www.kaggle.com/mrisdal/fake-news

size: 12999 items

used for: TextualClaims, DomainLabels

## `golbeck_fakenews`

type: url labels + rebuttals

url: https://github.com/jgolbeck/fakenews

size: 493 items

used for:
- fact_checking_urls: because the rebuttals linked belong to fact checking websites
- url_labels: because the urls have labels (`fake`/`satire`)
- Rebuttals

## `liar`

type: aggregator of politifact claimReviews. Columns (politifact_id, label, statement, subjects, speaker, speaker_job_title, state_info, party_affiliation, context)

url: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip

size: 12836 items

used for: fact_checking_urls, ClaimReviews

## `rumor`

type: twitter/weibo posts with label `rumor`/`otherwise`

url: http://alt.qcri.org/~wgao/data/rumdect.zip

size: 992 events

used for: url_labels (twitter urls can be built from tweet_id) TODO

## `fever`

type: aggregation of TextualClaim items with label `supported`/`refuted`/`notEnoughInfo` related to wikipedia page IDs as evidence

url: http://fever.ai/data.html

size: 185445 items

used for: nothing, TODO, can be used for learning relations between evidence and claims

## `hoaxy`

type: twitter retweets with labels `claim`/`fact_checking` related to the link contained

url: https://dataverse.mpi-sws.org/dataset.xhtml?persistentId=doi:10.5072/FK2/XSEHDL

size: 20987211 items

used for: TODO, can be used for fact_checking_urls

## `buzzface`

type: facebook posts (fb_url, type, rating, shares&likes&comments)

url: https://dataverse.mpi-sws.org/dataset.xhtml?persistentId=doi:10.5072/FK2/UP05PM

size: 2282 items

used for: url_labels (both fb urls and source URLs)

Posts have been fact-checked one by one.
The urls are to facebook. To extract source URLs:

1. filter type='link' in tsv
2. go to facebook url and parse html
3. filter a tabindex="-1" target="_blank"
4. take href, select queryParam 'u', unescape it
5. this is the link

## `fakenews_challenge`

type: stance detection: headlines with related full text pages and label `agrees`/`disagrees`/`discusses`/`unrelated`

url: http://www.fakenewschallenge.org/

size: 300 headlines against 2595 body texts

used for: TODO, can be used to learn to detect unrelated headlines (clickbait?)

## `fakenews_corpus`

type: news articles scraped from the `opensources` list + nytimes + webhose

url: https://github.com/several27/FakeNewsCorpus https://researchably-fake-news-recognition.s3.amazonaws.com/public_corpus/news_cleaned_2018_02_13.csv.zip

size: 9408908 articles

used for: nothing, simply use the domains from `opensources`

## `opensources`

type: DomainLabel list

url: http://www.opensources.co/

size: 834 domains

used for: DomainLabels

## `bs_detector`

type: DomainLabel list

url: https://github.com/bs-detector/bs-detector/blob/dev/ext/data/data.json

size: 722 domains

used for: DomainLabels

## `vlachos_factchecking`

type: TextualClaim list with some fact_checking_urls (politifact and channel4)

url: https://sites.google.com/site/andreasvlachos/resources/FactChecking_LTCSS2014_release.tsv?attredirects=0

size: 221 items

used for: fact_checking_urls, TextualClaims

## `hyperpartisan`

type: articles from `left`/`least`/`right` political side and labels (publisher-wise) coming from BuzzFeed journalists and MediaBiasFactCheck.com

url: https://pan.webis.de/semeval19/semeval19-web/

size: 1 milion items

used for: TODO, can be used for DomainLabels related to bias

## `rbutr`

type: urls with label and rebuttal urls

url: http://rbutr.com/

size: 16179 urls

used for: Rebuttals

## `fakenewsnet`

type: articles from buzzfeed and politifact (they are not linked in the data) with (title, url, author, ...)

url: https://github.com/KaiDMML/FakeNewsNet

size: 422 items

used for: url_labels, TextualClaims

## `fake_real_news_dataset`

type: articles (title, text, label)

url: https://github.com/GeorgeMcIntire/fake_real_news_dataset (dead)

size: 7795 items

used for: TODO TextualClaims

# `domain_list`

type: DomainLabels

url:

- `fakenewswatch` https://web.archive.org/web/20180213181029/http://fakenewswatch.com/
- `dailydot` https://www.dailydot.com/layer8/fake-news-sites-list-facebook/
- `usnwes` http://www.usnews.com/news/national-news/articles/2016-11-14/avoid-these-fake-news-sites-at-all-costs
- `newsrepublic` https://newrepublic.com/article/118013/satire-news-websites-are-cashing-gullible-outraged-readers
- `cbsnews` http://www.cbsnews.com/pictures/dont-get-fooled-by-these-fake-news-sites/
- `thoughtco` https://www.thoughtco.com/guide-to-fake-news-websites-3298824
- `npr` https://www.npr.org/sections/alltechconsidered/2016/11/23/503146770/npr-finds-the-head-of-a-covert-fake-news-operation-in-the-suburbs
- `snopes` https://www.snopes.com/news/2016/01/14/fake-news-sites/
- `politifact` https://www.politifact.com/punditfact/article/2017/apr/20/politifacts-guide-fake-news-websites-and-what-they/

size: 326 domains

used for: DomainLabels

## `melissa_zimdars`

type: DomainLabels

url: https://docs.google.com/document/d/10eA5-mCZLSS4MQY5QGb5ewC3VAL6pLkT53V_81ZyitM/preview

size: 1000 domains

used for: DomainLabels

## `wikipedia`

type: DomainLabels

url: https://en.wikipedia.org/wiki/List_of_fake_news_websites

size: 179 domains

used for: DomainLabels

## `credibilitycoalition`

type: ??

url: https://data.world/credibilitycoalition/webconf-2018

size: ??

used for: ??

## `credbank`

type: ??

url: http://compsocial.github.io/CREDBANK-data/

size: ??

used for: ??

## `some_like_it_hoax`

type: ??

url: https://github.com/gabll/some-like-it-hoax

size: ??

used for: ??

Not retrievable because of Facebook API and Cambridge Analytica

## `jruvika_fakenews

type: articles (urls, headline, body, label(1==true,0==fake))

url: https://www.kaggle.com/jruvika/fake-news-detection

size: 4009 items

used for: url_labels, TextualClaims

## `pontes_fakenewssample`

type: articles (domain, type, url, content, title, authors, source)

url: https://www.kaggle.com/pontes/fake-news-sample

size: 426550 items

used for: url_labels, TextualClaims

TODO see if the label always comes from the domain

## `incongruity`

type: ?? TODO analyse probably article headline and body

url: https://github.com/david-yoon/detecting-incongruity/

size: ??

used for: TextualClaims

## `osf_crowdsourcing`

type: DomainLabels

url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3118471 https://osf.io/6bptd/

size: 61 domains

used for: DomainLabels

## `factcheckni_list

type: article (title, url, date, claim, claim_url, conclusion, label, fb_stats) related to factcheckni

url: not available

size: 55 items

used for: fact_checking_urls

## `elections_integrity`

type: 10 milion tweets

url: https://about.twitter.com/en_us/values/elections-integrity.html#data

size: 10 milion tweets

used for: ??

## `buzzfeednews`

type: DomainLabels

url: https://github.com/BuzzFeedNews/2018-12-fake-news-top-50

size: 257 items

used for: DomainLabels
