#!/bin/bash
set -e

# date in format 2023_03_30
# TODAY=$(date +%Y_%m_%d)
# last day (get from API)

TODAY=0

while getopts d:h flag
do
    case "${flag}" in
        h) help=1;;
        d) if [[ "$OPTARG" =~ ^[0-9]{4}_[0-9]{2}_[0-9]{2}$ ]]; then
          TODAY=$OPTARG
          else
              echo "Date must be in format YYYY_MM_DD"
              exit 1
          fi;;
    esac
done

# check if today is set
if [ $TODAY = 0 ]; then
    echo "Date must be set with -d flag"
    exit 1
fi
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