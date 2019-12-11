
class Scraper(object):

    def __init__(self, configuration=None):
        self.configuration = configuration

    def scrape(self):
        raise NotImplementedError('override this method')
