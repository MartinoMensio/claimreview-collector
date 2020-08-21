# ClaimReview collector

This library can be used to deal with `claimReview` items:
- retrieve from aggregators
- scrape from fact-checkers
- normalize from other representations (e.g. n3 triples, microdata)
- get flattened simplified representation

## Requirements

Install this library with `pip` (that uses `setup.py`).
It is highly recommended (FOR NOW REQUIRED) that you have a MongoDB instance locally, so that the caching mechanism will make everything faster.

## How it works

`claimReview`s are published in different places:

- datacommons feeds
- fact checker websites
- ...

Each of the [origins](claimreviews/scrapers/) can either:

1. provide `claimReview` objects directly
2. provide a list of URLs that will contain the `claimReview`

While for the first group, the work of this project is just to aggregate them, the second requires scraping the pages and dealing with possibly broken metadata.

## Run the collection

Update all:

```bash
python -m claimreview_scraper.scrapers
```

Update commands for each origin:

```bash
python -m claimreview_scraper.scrapers.implementations.datacommons_feeds # 13567 ~ 10s
python -m claimreview_scraper.scrapers.implementations.datacommons_research_dataset # 5776
python -m claimreview_scraper.scrapers.implementations.esi_api # 674
python -m claimreview_scraper.scrapers.implementations.euvsdisinfo # 9099 ~ 2m 5s
python -m claimreview_scraper.scrapers.implementations.factcheck_org # 623 ~ 11m 33s
python -m claimreview_scraper.scrapers.implementations.factcheckni # 10 ~ 3m 29s
python -m claimreview_scraper.scrapers.implementations.fullfact # 826   ~1m 36s
python -m claimreview_scraper.scrapers.implementations.google_factcheck_explorer # 79490 ~3m 18s
python -m claimreview_scraper.scrapers.implementations.istinomer # 4179 ~ 14m 23s
python -m claimreview_scraper.scrapers.implementations.leadstories # 4876 ~ 9m 43s
python -m claimreview_scraper.scrapers.implementations.lemonde_decodex_hoax # 459 ~ 4s
python -m claimreview_scraper.scrapers.implementations.politifact # 1277 ~ 28m 22s
python -m claimreview_scraper.scrapers.implementations.snopes # 1252 ~ 36m 35s
python -m claimreview_scraper.scrapers.implementations.teyit_org # 1807
python -m claimreview_scraper.scrapers.implementations.weeklystandard # 102 ~ 43s
python -m claimreview_scraper.scrapers.implementations.poynter_covid ### the COVID-related collection (errors, not unified)

# SIZE indicated by db.getCollection('claim_reviews').distinct('url', {retrieved_by: 'COLLECTION_NAME'})
```

By fact-checker see table https://docs.google.com/spreadsheets/d/1etGJjS_l9iyWyWzBmqKYoGwz9_QKQKia4mUyfJWag9o/edit#gid=0

or Python
```python
from claimreview_scraper.scrapers import datacommons_feeds
s = datacommons_feeds.DatacommonsScraper()
claimreviews = s.scrape()
```

## Data information

For an approximate size of each of the origins, look at https://docs.google.com/spreadsheets/d/1etGJjS_l9iyWyWzBmqKYoGwz9_QKQKia4mUyfJWag9o/edit?pli=1#gid=0

## Useful queries

If you want to get from mongodb the ClaimReviews that match a certain query:

```bash
mongoexport -d claimreview_scraper -c claim_reviews -q '{url: /sciencefeedback|climatefeedback|healthfeedback/}' | sed '$!s/$/,/' > sciencefeedback.json
echo -e "[$(cat sciencefeedback.json)]" > sciencefeedback.json
```

## Dumps

```bash
mongodump -d claimreview_scraper -o dump
tar -zcvf dump.tar.gz dump
```

Import
```bash
tar -xvzf dump.tar.gz
mongorestore --db claimreview_scraper dump/claimreview_scraper
```

## TODOs

- unify the scraping: separate the collection of URLs where ClaimReviews are published and actual scraping of the pages
- merge the json cleanup tool that for now is run on this docker https://github.com/MartinoMensio/dirtyjson
- validate and normalise JSON-LD with respect to the schema
