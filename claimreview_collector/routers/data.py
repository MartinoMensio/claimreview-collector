from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException, Query
from starlette.responses import FileResponse
from pydantic import BaseModel


from ..processing import (
    utils,
    extract_claim_reviews,
    extract_tweet_reviews,
    database_builder,
    cache_manager,
    ukraine_retrieve,
)
from .. import scrapers
from ..publishing import github

from ..main import ROLE

router = APIRouter()

from ..processing import data_manager


class StatsBody(BaseModel):
    date: str
    # scrapers_stats: Dict[str, int]
    # claim_reviews: Dict[str, int]
    # tweet_reviews: Dict[str, int]
    # files: Dict[str, str]


@router.get("/daily")
def list_data(since: Optional[str] = None, until: Optional[str] = None):
    return data_manager.list_data(since, until)


@router.get("/daily/{date}")
def get_data(date: str = "latest", file: Optional[str] = None):
    if file:
        file_path = data_manager.get_data_file_path(file, date)
        file_name = file_path.split("/")[-1]
        file_response = FileResponse(file_path, filename=file_name)
        return file_response
    else:
        index_entry = data_manager.get_index_entry(date)
        return index_entry


@router.post("/download")
def download_data(stats: StatsBody):
    # download asset
    date = stats.date
    data_manager.download_data(date)
    return {"status": "ok"}


@router.get("/latest_factchecks")
def get_latest_factchecks():
    return data_manager.get_latest_factchecks()


@router.get("/sample")
def random_sample(
    since: Optional[str] = "2019-01-01",
    until: Optional[str] = None,
    misinforming_domain: Optional[str] = None,
    fact_checker_domain: Optional[str] = None,
    exclude_misinfo_domain: Optional[List[str]] = Query(
        ["twitter.com", "wikipedia.org"]
    ),
    exclude_homepage_url_misinfo: Optional[bool] = True,
    cursor: Optional[int] = None,
):
    result = data_manager.random_sample(
        since,
        until,
        misinforming_domain,
        fact_checker_domain,
        exclude_misinfo_domain,
        exclude_homepage_url_misinfo,
        cursor,
    )
    if not result:
        raise HTTPException(404, "no items with the used filters")

    return result


@router.post("/update")
def update_data():
    # already checked up that this is ROLE==full
    if ROLE == "light":
        raise HTTPException(status_code=400, detail="light instance cannot update")
    return data_manager.update_data()


@router.post("/update/ukraine")
def update_ukraine(stats: StatsBody):
    # already checked up that this is ROLE==full
    if ROLE == "light":
        raise HTTPException(status_code=400, detail="light instance cannot update")
    # download_data(stats)
    return ukraine_retrieve.collect(stats.date)
