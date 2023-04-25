#!/bin/bash
set -e

# date in format 2023_03_30
# TODAY=$(date +%Y_%m_%d)
# last day (get from API)
TODAY=2023_04_19
TODAY_FOLDER=ukraine_archive/ukraine_$TODAY
mkdir -p $TODAY_FOLDER

# IFCN data

echo "Getting IFCN data..."
# get latest data
curl -f -X 'POST' \
  'http://localhost:20400/data/download' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"date": "'$TODAY'"}'
echo "Running clean_sample_ukraine.py..."
python clean_sample_ukraine.py
mv ukraine.tsv $TODAY_FOLDER/ukraine_IFCN.tsv


# EUvsDisinfo data
echo "Getting EUvsDisinfo data..."
set +e
python -m claimreview_collector.scrapers.implementations.euvsdisinfo
echo Getting EUvsDisinfo data again...
set -e
python -m claimreview_collector.scrapers.implementations.euvsdisinfo
echo "Running clean_sample_ukraine.py..."
python clean_sample_ukraine.py
mv ukraine.tsv $TODAY_FOLDER/ukraine_euvsdisinfo.tsv


# UkraineFacts data
echo "Getting UkraineFacts data..."
python -m claimreview_collector.scrapers.implementations.ukrainefacts
mv ukraine_ukrainefacts.tsv $TODAY_FOLDER/ukraine_ukrainefacts.tsv

echo "Done!"