# ClaimReview collector

This library can be used to deal with `claimReview` items:
- retrieve from aggregators
- scrape from fact-checkers
- normalize from other representations (e.g. n3 triples, microdata)
- get flattened simplified representation

## Requirements

Install this library with:
```
pip install pdm
pdm install
```

It is highly recommended (FOR NOW REQUIRED) that you have a MongoDB instance locally, so that the caching mechanism will make everything faster.

### FlareSolverrr

https://github.com/FlareSolverr/FlareSolverr

docker run -d \
  --name=mm35626_flaresolverr \
  -p 127.0.0.1:8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest

### DirtyJSON

docker run -dit --restart always --name mm35626_dirtyjson -p 127.0.0.1:12345:12345 martinomensio/dirtyjson


## Dump management

Create dump:
```bash
mongodump -d claimreview_collector -o dumps/latest
pushd dumps
tar -zcvf latest.tar.gz latest
popd
```

Transfer dump:
```bash
scp ./dumps/latest.tar.gz kmi-appsvr04:/data/user-data/mm35626/claimreview-collector/dumps/latest.tar.gz
```

Import db
```bash
pushd dumps
tar -xvzf latest.tar.gz
popd
docker run --rm --name mm35626_mongoimporter -v `pwd`/dumps:/dumps --link=mm35626_mongo:mongo -it mongo bash
mongorestore --host mongo --db claimreview_collector dumps/latest/claimreview_collector

## Docker installation and running
docker build . -t martinomensio/claimreview-collector
# local light (no link, using local misinfome). Start before misinfo_server
# mapping the source code as volume overwriting, so can restart and test easily
docker run --restart always -it --name mm35626_claimreview_collector_light -v `pwd`/.env:/app/.env -v `pwd`/data:/app/data -v `pwd`/claimreview_collector:/app/claimreview_collector --link=mm35626_mongo:mongo -e MONGO_HOST=mongo:27017 -p 20400:8000 -e ROLE=light martinomensio/claimreview-collector
# local full (no auto-restart)
# mapping the source code as volume overwriting, so can restart and test easily
docker run -it --name mm35626_claimreview_collector_full -v `pwd`/data:/app/data -v `pwd`/.env:/app/.env -v `pwd`/claimreview_collector:/app/claimreview_collector --link=mm35626_flaresolverr:flaresolverr -e FLARESOLVERR_HOST=flaresolverr --link=mm35626_mongo:mongo -e MONGO_HOST=mongo:27017 -e MISINFO_BACKEND="http://misinfo_server:5000" --link=mm35626_misinfo_server:misinfo_server -e TWITTER_CONNECTOR="http://misinfo_server:5000/misinfo/api/twitter" -e DIRTYJSON_REST_ENDPOINT="http://dirtyjson_server:12345" --link=mm35626_dirtyjson:dirtyjson_server -p 20500:8000 -e ROLE=full martinomensio/claimreview-collector
# server web (ROLE=light) no need of twitter or misinfo backend. But need of credibility backend
docker run --restart always -it --name mm35626_claimreview_collector_light -v `pwd`/.env:/app/.env -v `pwd`/data:/app/data --link=mm35626_mongo:mongo -e MONGO_HOST=mongo:27017 -p 127.0.0.1:20400:8000 -e ROLE=light martinomensio/claimreview-collector
# server (ROLE=full) without link to twitter_connector, using the public misinfome API. Credibility need for IFCN only (through misinfomeAPI)
docker run --restart always -it --name mm35626_claimreview_collector_full -v `pwd`/.env:/app/.env -v `pwd`/data:/app/data --link=mm35626_flaresolverr:flaresolverr -e FLARESOLVERR_HOST=flaresolverr:8191 --link=mm35626_mongo:mongo -e MONGO_HOST=mongo:27017 -e MISINFO_BACKEND="https://misinfo.me" -e TWITTER_CONNECTOR="https://misinfo.me/misinfo/api/twitter" -e DIRTYJSON_REST_ENDPOINT="http://dirtyjson_server:12345" --link=mm35626_dirtyjson:dirtyjson_server -p 127.0.0.1:20500:8000 -e ROLE=full -e PUBLISH_GITHUB=true martinomensio/claimreview-collector


# Auto-update
Huge:
claimreview-collector_huge (ROLE=full) creates release and publishes to GitHub
claimreview-collector_huge sends POST to cr2_light with:
       - date
       - stats

Light (ROLE=light):
- receive POST from huge (misinfo/api/data --> claimreview_collector)
- download from GitHub, extract
- make files available from API (fix the files entries)
- clean from API data old (delete others from more than a week? Or only keep zips?)
Then import inside mongo:
mongoimport --db claimreview_collector --collection claim_reviews_test --file data/latest/claim_reviews_raw.json --jsonArray
Then trigger credibility endpoints

ROLE=light has:
- scheduler disabled
- POST data/update (collect) disabled
- POST data/download enabled
- all the zips and files stored
ROLE=full has:
- scheduler enabled
- POST data/update enabled
- POST data/download enabled (for recovery???)
- only the latest zip and files stored

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
python -m claimreview_collector.scrapers
```

Update commands for each origin:

```bash
python -m claimreview_collector.scrapers.implementations.datacommons_feeds # 19161 ~ 10s
python -m claimreview_collector.scrapers.implementations.datacommons_research_dataset # 5776
python -m claimreview_collector.scrapers.implementations.esi_api # 674 (not available outside OU) --> REMOVED, too wrong!
python -m claimreview_collector.scrapers.implementations.euvsdisinfo # 13616 ~ 2m 5s
python -m claimreview_collector.scrapers.implementations.factcheck_org # 623 ~ 11m 33s (not using sharethefacts anymore)
python -m claimreview_collector.scrapers.implementations.factcheckni # 21 ~ 3m 29s
python -m claimreview_collector.scrapers.implementations.fullfact # 855   ~1m 36s
python -m claimreview_collector.scrapers.implementations.google_factcheck_explorer # 99828 ~3m 18s
python -m claimreview_collector.scrapers.implementations.istinomer # 4179 ~ 14m 23s (ERROR: microdata does not contain anymore full ClaimReview)
python -m claimreview_collector.scrapers.implementations.leadstories # 5219 ~ 9m 43s
python -m claimreview_collector.scrapers.implementations.lemonde_decodex_hoax # 479 ~ 4s
python -m claimreview_collector.scrapers.implementations.politifact # 1263 ~ 28m 22s
python -m claimreview_collector.scrapers.implementations.snopes # 1530 ~ 36m 35s
python -m claimreview_collector.scrapers.implementations.teyit_org # 2375 ~ 1m 27s
python -m claimreview_collector.scrapers.implementations.weeklystandard # 102 ~ 43s
python -m claimreview_collector.scrapers.implementations.poynter_covid # 9992 ~ 18m 17s
python -m claimreview_collector.scrapers.implementations.chequeado # 1179 ~ 49m 0s

# SIZE indicated by db.getCollection('claim_reviews').distinct('url', {retrieved_by: 'COLLECTION_NAME'})
```

Run server: 
```bash
uvicorn claimreview_collector.main:app --reload
```

By fact-checker see table https://docs.google.com/spreadsheets/d/1etGJjS_l9iyWyWzBmqKYoGwz9_QKQKia4mUyfJWag9o/edit#gid=0

or Python
```python
from claimreview_collector.scrapers import datacommons_feeds
s = datacommons_feeds.DatacommonsScraper()
claimreviews = s.scrape()
```

## Data information

For an approximate size of each of the origins, look at https://docs.google.com/spreadsheets/d/1etGJjS_l9iyWyWzBmqKYoGwz9_QKQKia4mUyfJWag9o/edit?pli=1#gid=0

## Useful queries

If you want to get from mongodb the ClaimReviews that match a certain query:

```bash
mongoexport -d claimreview_collector -c claim_reviews -q '{url: /sciencefeedback|climatefeedback|healthfeedback/}' | sed '$!s/$/,/' > sciencefeedback.json
echo -e "[$(cat sciencefeedback.json)]" > sciencefeedback.json
```

## TODOs

- unify the scraping: separate the collection of URLs where ClaimReviews are published and actual scraping of the pages
- merge the json cleanup tool that for now is run on this docker https://github.com/MartinoMensio/dirtyjson
- validate and normalise JSON-LD with respect to the schema

