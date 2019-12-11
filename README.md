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

```bash
python -m datasets scrape_factchecking
```

Or to run a single scraper:

```
python -m datasets scrape_single_factchecking $NAME
```

Updated instructions by origin
```bash
python -m claimreview_scraper.scrapers.datacommons_feeds # 3406
python -m claimreview_scraper.scrapers.datacommons_research_dataset # 11501 (from 5764 initial + 5737 full rescraped)
python -m claimreview_scraper.scrapers.esi_api # 1311
python -m claimreview_scraper.scrapers.euvsdisinfo # 7053
python -m claimreview_scraper.scrapers.factcheck_org # 623 (from 2280 urls) (distinct url in datasets_resources.claim_reviews: 1120, claimreview_scraper.claim_reviews: 1095)
python -m claimreview_scraper.scrapers.factcheckni # useless, no ClaimReview here (85 vs 79 old)
python -m claimreview_scraper.scrapers.fullfact # 924 (from 689 urls) (1439 vs 1348)
python -m claimreview_scraper.scrapers.google_factcheck_explorer # 45822
python -m claimreview_scraper.scrapers.istinomer # 4077 (from 4077 urls)
python -m claimreview_scraper.scrapers.leadstories # 1754 (from 4217 urls)
python -m claimreview_scraper.scrapers.lemonde_decodex_hoax # 371
python -m claimreview_scraper.scrapers.politifact # 3981 (from 16770 urls)
python -m claimreview_scraper.scrapers.snopes # 350 (from 8204 urls)
python -m claimreview_scraper.scrapers.teyit_org # 1187 (from 1197 urls)
python -m claimreview_scraper.scrapers.weeklystandard # 129 (from 170 urls)
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
mongoexport -d datasets_resources -c claim_reviews -q '{url: /sciencefeedback|climatefeedback|healthfeedback/}' | sed '$!s/$/,/' > sciencefeedback.json
echo -e "[$(cat sciencefeedback.json)]" > sciencefeedback.json
```


## TODOs

- unify the scraping: separate the collection of URLs where ClaimReviews are published and actual scraping of the pages
- merge the json cleanup tool that for now is run on this docker https://github.com/MartinoMensio/dirtyjson
- validate and normalise JSON-LD with respect to the schema
