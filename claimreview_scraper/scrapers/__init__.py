import pkgutil

from . import implementations

class ScraperBase(object):
    id: str
    homepage: str
    name: str
    description: str

    def __init__(self, configuration=None):
        self.configuration = configuration

    def scrape(self):
        raise NotImplementedError('override this method')

def scrape_all():
    scrapers = {}
    # get all the modules in the implementations package
    for importer, modname, ispkg in pkgutil.iter_modules(implementations.__path__, implementations.__name__ + "."):
        module = __import__(modname, fromlist="dummy")
        if hasattr(module, 'Scraper'):
            s: ScraperBase = module.Scraper()
            scrapers[s.id] = s
            print(s.id)
        else:
            print('module', module, 'does not have an implementation of ScraperBase')
    # scrapers = {k: v for i, (k, v) in enumerate(scrapers.items()) if i >= 12}
    for k,v in scrapers.items():
        print('scraping', k)
        v.scrape()
