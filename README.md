
# Datasets

This folder contains the different datasets that we collected.

The goal is to acquire as many as possible urls with a label that tells if they are true or fake.

For this purpose we use a binary lable (true or fake).

We select from the datasets only items that are (almost) completely true or fake, removing the variations in the middle.

Goal: have a list of URL labelled with `fake` / `true`

## `datacommons_factcheck`

source url: `https://www.datacommons.org/factcheck/download`

This is a collection of claimReviews. The problem is that they contain fewer attributes than the claimReviews that are published on the fact-checking websites. For this reason the fact checker websites are scraped to obtain the full claimReview.

## datacommons_feeds

source url: `https://storage.googleapis.com/datacommons-feeds/claimreview/latest/data.json`

labels:

majority: ratingValue between worstRating and bestRating
factcheckni: alternateName text
  false: "False.", "Misleading", "This claim is false", "Mostly false."
  true: "True", "Accurate", "The claim is accurate", "The claim is true"
  other: "Unproven", "Inaccurate.", "Correct with consideration.", "Partly accurate", "Broadly accurate", "Uncertain"

problem: the URL is to fact checker, not the source

conclusion: not used

## `liar`

source url: `https://www.cs.ucsb.edu/~william/data/liar_dataset.zip`

labels are ok

source urls: not present in the dataset, but there are links to politifacts


## `golbeck_fakenews`

success!

## `fever`

No URLs, just claims as text

## `buzzface`

the urls are to facebook.

1. filter type='link' in tsv
2. go to facebook url and parse html
3. filter a tabindex="-1" target="_blank"
4. take href, select queryParam 'u', unescape it
5. this is the link

success!

## `several27_fakenews_corpus`

source: https://github.com/several27/FakeNewsCorpus --> http://researchably-fake-news-recognition.s3.amazonaws.com/public_corpus/news_cleaned_2018_02_13.csv.zip

