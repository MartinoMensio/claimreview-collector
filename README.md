# ClaimReview collector

We want all the `claimReview` items!

## How it works

`claimReview`s are published in different places:

- datacommons feeds
- fact checker websites
- ...

Each of the [origins](claimreviews/scrapers/) can either:

1. provide `claimReview` objects directly
2. provide a list of URLs that will contain the `claimReview`

While for the first group, the work of this project is just to aggregate them, the second requires scraping the pages and dealing with possibly broken metadata.


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
