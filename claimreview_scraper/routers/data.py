import os
import glob
from pathlib import Path
import shutil
import datetime
from typing import Optional
from fastapi import APIRouter
from starlette.responses import FileResponse

from ..processing import utils, extract_claim_reviews, extract_tweet_reviews
from .. import scrapers
from claimreview_scraper import processing 

router = APIRouter()

base_path = os.getcwd()
folder = 'data'
index_path = f'{folder}/index.json'
latest_data_path = f'{folder}/latest'

@router.get('/')
def list_data(since: Optional[str] = None, until: Optional[str] = None):
    if os.path.isfile(index_path):
        items = utils.read_json(index_path)
    else:
        items = {}
    # TODO filtering since and until
    if since:
        items = {k:v for k,v in items.items() if k >= since}
    if until:
        items = {k:v for k,v in items.items() if k <= until}
    return items

# @router.get('/latest')
# def get_latest_data():
#     pass

@router.get('/{date}')
def get_data(date: str = 'latest', file: Optional[str] = None):
    # if date == 'latest':
    # convert latest ?
    data_entries = list_data()
    if date not in data_entries:
        # TODO manage errors
        return "nothing for that date"
    data = data_entries[date]
    if not file:
        return data
    if file not in data:
        # TODO manage errors
        return "no such file, remove this parameter to see the available files"
    # extension = 'zip' if file == 'zip' else 'json'
    # file_name = file if file != 'zip' else date
    file_name = data[file]
    file_path = f'{folder}/{date}/{file_name}'
    print(file_path)
    if not os.path.isfile(file_path):
        # TODO manage errors
        return "file not found on disk"
    file_response = FileResponse(file_path, filename=file_name)
    return file_response

@router.post('/update')
def update_data():
    result_stats = {}
    today = datetime.datetime.today().strftime('%Y_%m_%d')  # TODO yyyy_mm_dd
    print('today', today)
    zip_path = f'{folder}/{today}.zip'
    today_path = f'{folder}/{today}'

    # run scrapers
    stats_scrapers = scrapers.scrape_daily()
    result_stats['scrapers_stats'] = stats_scrapers
    # extract
    # TODO keep stats
    cr_stats = extract_claim_reviews.extract_ifcn_claimreviews()
    tw_stats = extract_tweet_reviews.extract() # TODO this is the slowest, keep the tweets cached in twitter_connector
    result_stats['claim_reviews'] = cr_stats
    result_stats['tweet_reviews'] = tw_stats


    # zip everything
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    make_archive(latest_data_path, f'{today_path}.zip')

    # copy latest to today folder
    if os.path.isdir(today_path):
        shutil.rmtree(today_path)
    shutil.copytree(latest_data_path,today_path)

    files = glob.glob(f'{today_path}/**')
    files = {f.split('/')[-1].replace('.json', ''): f for f in files}
    files['zip'] = zip_path

    result_stats['files'] = files

    # save index
    index = list_data()
    index[today] = result_stats
    index['latest'] = result_stats
    utils.write_json_with_path(index, Path(folder), 'index.json')

    return result_stats


def make_archive(source, destination):
    # http://www.seanbehan.com/how-to-use-python-shutil-make_archive-to-zip-up-a-directory-recursively-including-the-root-folder/
    base = os.path.basename(destination)
    name = base.split('.')[0]
    format = base.split('.')[1]
    archive_from = os.path.dirname(source)
    archive_to = os.path.basename(source.strip(os.sep))
    print(source, destination, archive_from, archive_to)
    shutil.make_archive(name, format, archive_from, archive_to)
    shutil.move('%s.%s'%(name,format), destination)
