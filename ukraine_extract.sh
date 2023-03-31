set -e

# date in format 2023_03_30
# TODAY=$(date +%Y_%m_%d)
TODAY=2023_03_30
TODAY_FOLDER=ukraine_archive/ukraine_$TODAY
mkdir -p $TODAY_FOLDER

# IFCN data

# get latest data
curl -X 'POST' \
  'http://localhost:20400/data/download' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "date": "2023_03_30"
}'
python clean_sample_ukraine.py
mv ukraine.tsv $TODAY_FOLDER/ukraine_IFCN.tsv


# EUvsDisinfo data
python -m claimreview_scraper.scrapers.implementations.euvsdisinfo
python clean_sample_ukraine.py
mv ukraine.tsv $TODAY_FOLDER/ukraine_euvsdisinfo.tsv


# UkraineFacts data
python -m claimreview_scraper.scrapers.implementations.ukrainefacts
mv ukraine_ukrainefacts.tsv $TODAY_FOLDER/ukraine_ukrainefacts.tsv