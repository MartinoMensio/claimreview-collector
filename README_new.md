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
