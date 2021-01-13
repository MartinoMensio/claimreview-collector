# from . import *

class ScraperBase(object):
    id: str
    homepage: str
    name: str
    description: str

    def __init__(self, configuration=None):
        self.configuration = configuration

    def scrape(self):
        raise NotImplementedError('override this method')