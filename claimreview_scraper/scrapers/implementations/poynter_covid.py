import csv
import tqdm
import requests
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'
}

# TODO uniform to the other scrapers
def scrape():
    page_n = 1
    results = []
    while True:
        url = f'https://www.poynter.org/ifcn-covid-19-misinformation/page/{page_n}/?orderby=views&order=ASC#038;order=ASC'

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        rows = soup.select('article')
        print(f'Found {len(rows)} articles at page {page_n}')
        if not len(rows):
            break

        with ThreadPool(8) as pool:
        
            for el in tqdm.tqdm(pool.imap(extract_row, rows), total=len(rows)):
                results.append(el)
        
        page_n += 1

    with open('poynter_covid.tsv', 'w') as f:
        writer = csv.DictWriter(f, el.keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(results)

def extract_row(r):
    checked_by = r.select_one('header.entry-header p.entry-content__text').text.strip().replace('Fact-Checked by: ', '')
    date, location = [el.strip() for el in r.select_one('header.entry-header p.entry-content__text strong').text.split('|')]

    title_el = r.select_one('h2.entry-title a')
    label_and_title = title_el.text.strip()
    label = label_and_title.split(':')[0]
    title = label_and_title.replace(label, '')[2:].strip()
    poynter_url = title_el['href']

    el = {
        'checked_by': checked_by,
        'date': date,
        'location': location,
        'label': label,
        'title': title,
        'poynter_url': poynter_url
    }

    # Explanation, fact-checker_url and origin are on the detail page
    response = requests.get(poynter_url, headers=headers)
    response.raise_for_status()
    #print(response.text)
    soup = BeautifulSoup(response.text, 'lxml')

    explanation = soup.select_one('p.entry-content__text--explanation').text.replace('Explanation: ', '').strip()
    originated_from = soup.select_one('p.entry-content__text--smaller').text.split(':')[-1].strip()
    factchecker_url = soup.select_one('a.entry-content__button--smaller')['href']

    el['explanation'] = explanation
    el['originated_from'] = originated_from
    el['factchecker_url'] = factchecker_url
    return el



def main():
    scrape()

if __name__ == "__main__":
    main()