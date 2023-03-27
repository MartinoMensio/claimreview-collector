import pkgutil
import tqdm

from . import implementations
from .implementations import (
    datacommons_feeds,
    google_factcheck_explorer,
    euvsdisinfo,
    factcheckni,
    fullfact,
    teyit_org,
)
from ..processing import database_builder


def scrape_all():
    scrapers = {}
    # get all the modules in the implementations package
    for importer, modname, ispkg in pkgutil.iter_modules(
        implementations.__path__, implementations.__name__ + "."
    ):
        module = __import__(modname, fromlist="dummy")
        if hasattr(module, "Scraper"):
            s = module.Scraper()
            scrapers[s.id] = s
            print(s.id)
        else:
            print("module", module, "does not have an implementation of ScraperBase")
    # scrapers = {k: v for i, (k, v) in enumerate(scrapers.items()) if i >= 12}
    for k, v in scrapers.items():
        print("scraping", k)
        try:
            v.scrape()
        except Exception as e:
            print(e)


def scrape_daily():
    # TODO manage scheduling
    scrapers = [
        datacommons_feeds.Scraper(),
        google_factcheck_explorer.Scraper(),
        # euvsdisinfo.Scraper(),
        # factcheckni.Scraper(),
        # fullfact.Scraper(),
        # teyit_org.Scraper(),
    ]
    stats = {}
    for s in tqdm.tqdm(scrapers, desc="scraping"):
        s.scrape()
        stat = database_builder.get_count_unique_from_scraper(s.id)
        stats[s.id] = stat

    # stats = database_builder.get_count_unique_from_scraper('datacommons_feeds')

    print(stats)
    return stats


def scrape_single_scraper(scraper_name: str):
    pass
