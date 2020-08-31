import requests
import tqdm

# https://chequeado.com/latamcoronavirus/
# (espanish) wget https://spreadsheets.google.com/feeds/list/1mMf5y2_CvlbTCzgE6EA6ZhFR7RAvTXhd1713kUpIPOw/od6/public/values?alt=json
# (portuguese) wget https://spreadsheets.google.com/feeds/list/1BIgVzAcMhWXR5oW9c1UB2vnW5RY6vni_FRXvBaAG_4Q/od6/public/values?alt=json
# (other data??) wget https://docs.google.com/spreadsheets/d/1Uj78PbPqcskXrjk3d3nGUvfq_6tN1vWbRraq4je7AyQ/edit#gid=0 

from .. import ScraperBase
from ...processing import utils
from ...processing import claimreview
from ...processing import database_builder

class Scraper(ScraperBase):
    def __init__(self):
        self.id = 'chequeado'
        self.homepage = 'https://chequeado.com/latamcoronavirus/'
        self.name = 'Información chequeada sobre el Coronavirus'
        self.description = 'Frente a la “infodemia”, la difusión de rumores y noticias contenidos falsos, los chequeadores de Latinoamérica nos aliamos para compartir la información que producimos y, al unir esfuerzos, brindar mejor información a nuestras comunidades. Las desinformaciones que circulan en muchos casos son las mismas en distintos países y poder contar con el trabajo de otros ayuda a desmentir más rápidamente las falsedades y evitar su propagación.\nLas notas que están publicadas en esta base pueden ser reutilizadas libremente siempre que se cite y ponga el link a la nota original.'
        ScraperBase.__init__(self)

    def scrape(self, update=True):
        if update:
            es_reviews = scrape_all(self.id, 'https://spreadsheets.google.com/feeds/list/1mMf5y2_CvlbTCzgE6EA6ZhFR7RAvTXhd1713kUpIPOw/od6/public/values?alt=json')
            pt_reviews = scrape_all(self.id, 'https://spreadsheets.google.com/feeds/list/1BIgVzAcMhWXR5oW9c1UB2vnW5RY6vni_FRXvBaAG_4Q/od6/public/values?alt=json')
            all_reviews = es_reviews + pt_reviews
        else:
            all_reviews = database_builder.get_original_data(self.id)
            all_reviews = list(all_reviews)
        
        claim_reviews = []
        for r in tqdm.tqdm(all_reviews):
            try:
                # the es and pt have different field names
                url_fixed, cr = claimreview.retrieve_claimreview(r.get('Link al chequeo', r.get('Link para a checagem')))
                # cr = create_claimreview(r, self.id)
                claim_reviews.extend(cr)
            except Exception as e:
                pass
        # TODO pymongo.errors.BulkWriteError: batch op errors occurred
        database_builder.add_ClaimReviews(self.id, claim_reviews)

def scrape_all(self_id, gdrive_url):
    response = requests.get(gdrive_url)
    response.raise_for_status()
    
    table = response.json()

    cleaned_table = []
    for row in table['feed']['entry']:
        properties = {k[4:].replace('.', '_'): v['$t'].strip() for k, v in row.items() if k.startswith('gsx$')}
        cleaned_table.append(properties)

    results = []
    # the first line contains the headers
    headers = cleaned_table[0]
    table_rows = cleaned_table[1:]
    for r in table_rows:
        results.append({headers[k]: v for k, v in r.items()})

    database_builder.save_original_data(self_id, results)

    print(len(results), 'retrieved')

    return results


def main():
    scraper = Scraper()
    scraper.scrape()

if __name__ == "__main__":
    main()