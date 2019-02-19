from ..processing import aggregate
from ..processing.datasets import datacommons_factcheck, datacommons_feeds, mrisdal_fakenews, golbeck_fakenews, liar, buzzface, opensources, fakenewsnet, rbutr, hyperpartisan, wikipedia, domain_list, jruvika_fakenews, factcheckni_list, buzzfeednews, pontes_fakenewssample, vlachos_factchecking  # datasets, factchecking_scrapers, fact_checker_lists
from ..processing.scrapers import google_factcheck_explorer, factcheckni, fullfact, leadstories, politifact, snopes, weeklystandard
from ..processing.fact_checker_lists import ifcn, reporterslab

processing_functions_datasets = {
    'datacommons_factcheck': datacommons_factcheck.main,
    'datacommons_feeds': datacommons_feeds.main,
    'mrisdal_fakenews': mrisdal_fakenews.main,
    'golbeck_fakenews': golbeck_fakenews.main,
    'golbeck_fakenews': golbeck_fakenews.main,
    'liar': liar.main,
    'hoaxy': lambda: None, # TODO
    'buzzface': buzzface.main,
    'opensources': lambda: opensources.main('opensources'),
    'fakenewsnet': fakenewsnet.main,
    'rbutr': rbutr.main,
    'hyperpartisan': hyperpartisan.main,
    'wikipedia': wikipedia.main,
    'domain_list_cbsnews': lambda: domain_list.main('cbsnews'),
    'domain_list_dailydot': lambda: domain_list.main('dailydot'),
    'domain_list_fakenewswatch': lambda: domain_list.main('fakenewswatch'),
    'domain_list_newrepublic': lambda: domain_list.main('newrepublic'),
    'domain_list_npr': lambda: domain_list.main('npr'),
    'domain_list_snopes': lambda: domain_list.main('snopes'),
    'domain_list_thoughtco': lambda: domain_list.main('thoughtco'),
    'domain_list_usnews': lambda: domain_list.main('usnews'),
    'domain_list_politifact': lambda: domain_list.main('politifact'),
    'melissa_zimdars': lambda: opensources.main('melissa_zimdars'),
    'jruvika_fakenews': jruvika_fakenews.main,
    'factcheckni_list': factcheckni_list.main,
    'buzzfeednews': buzzfeednews.main,
    'pontes_fakenewssample': pontes_fakenewssample.main,
    'vlachos_factchecking': vlachos_factchecking.main,
    'hearvox_unreliable_news': lambda: None # TODO
}

scrape_factchecking_functions = {
    'google_factcheck_explorer': lambda: google_factcheck_explorer.main(True),
    'factcheckni': factcheckni.main,
    'fullfact': fullfact.main,
    'leadstories': leadstories.main,
    'politifact': politifact.main,
    'snopes': snopes.main,
    'weeklystandard': weeklystandard.main
}

scrape_factcheckers_functions = {
    'ifcn': ifcn.main,
    'reporterslab': lambda: reporterslab.main(True)
}

def process_all():
    scrape_factchecking()
    process_factchecker_lists()
    process_datasets()
    aggregate_all()

def aggregate_all():
    print('aggregating all the data...')
    aggregate.main()
    print('aggregating all the data done')

def scrape_factchecking():
    print('scraping factchecking...')
    for key in scrape_factchecking_functions.keys():
        scrape_single_factching(key)
    print('scraping factchecking done')

def scrape_single_factching(key):
    print('processing {}...'.format(key))
    scrape_factchecking_functions[key]()
    print('done {}'.format(key))

def process_factchecker_lists():
    print('processing factckeckers list...')
    for key in scrape_factcheckers_functions.keys():
        process_single_factchecker_list(key)
    print('processing factcheckers list done')

def process_single_factchecker_list(key):
    print('processing {}...'.format(key))
    scrape_factcheckers_functions[key]()
    print('done {}'.format(key))

def process_datasets():
    print('processing datasets...')
    for key in processing_functions_datasets.keys():
        process_single_dataset(key)
    print('processing datasets done')

def process_single_dataset(key):
    print('processing {}...'.format(key))
    processing_functions_datasets[key]()
    print('done {}'.format(key))
