from ..processing import utils
from ..processing import aggregate
from ..processing.datasets import datacommons_factcheck, mrisdal_fakenews, golbeck_fakenews, liar, buzzface, opensources, fakenewsnet, rbutr, hyperpartisan, wikipedia, domain_list, jruvika_fakenews, factcheckni_list, buzzfeednews, pontes_fakenewssample, vlachos_factchecking  # datasets, factchecking_scrapers, fact_checker_lists
from ..scrapers import esi_api, google_factcheck_explorer, datacommons_feeds, factcheckni, fullfact, leadstories, politifact, snopes, weeklystandard, metafact, truthsetter, fiskkit, euvsdisinfo, lemonde_decodex_hoax, teyit_org, istinomer, kallxo_kripometer
from ..processing.fact_checker_lists import ifcn, reporterslab
from ..processing import database_builder

processing_functions_datasets = {
    'datacommons_factcheck': datacommons_factcheck.main,
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
    'esi_api': esi_api.main,
    'datacommons_feeds': datacommons_feeds.main,
    'factcheckni': factcheckni.main,
    'fullfact': fullfact.main,
    'leadstories': leadstories.main,
    'politifact': politifact.main,
    'snopes': snopes.main,
    'weeklystandard': weeklystandard.main,
    'metafact': metafact.main,
    'truthsetter': truthsetter.main,
    #'fiskkit': fiskkit.main
    'euvsdisinfo': euvsdisinfo.main,
    'lemonde_decodex_hoax': lemonde_decodex_hoax.main,
    'teyit_org': teyit_org.main,
    'istinomer': istinomer.main,
    'kallxo_kripometer': kallxo_kripometer.main
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
        scrape_single_factchecking(key)
    print('scraping factchecking done')

def scrape_single_factchecking(key):
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

def find_processing_function(key):
    if key in scrape_factcheckers_functions:
        return scrape_factcheckers_functions[key]
    elif key in scrape_factchecking_functions:
        return scrape_factcheckers_functions[key]
    elif key in processing_functions_datasets:
        return processing_functions_datasets[key]
    else:
        raise ValueError(key)

def retrieve_graph_edges(reprocess=False):
    print('retrieving graph edges, reprocess = ', reprocess)
    sources = utils.read_sources()

    graph = {
        'nodes': {},
        'links': []
    }

    fact_checking_urls = utils.read_json(utils.data_location / 'aggregated_fact_checking_urls.json')
    graph = claimreview.extract_graph_edges(fact_checking_urls)

    for s_key, s in sources.items():
        if s.get('graph_enabled', None):
            # this source has been prepared for credibility graph
            # so do what it requires
            processing_function = find_processing_function(s_key)
            if reprocess:
                processing_function()
            # and then collect the nodes and edges
            subgraph = utils.read_json(utils.data_location / s_key / 'graph.json')
            # TODO manage merge of nodes
            graph['nodes'].update(subgraph['nodes'])
            graph['links'].extend(subgraph['links'])

    utils.write_json_with_path(graph, utils.data_location, 'graph.json')

def save_graph_in_db():
    graph = utils.read_json(utils.data_location / 'graph.json')
    database_builder.save_graph(graph)


def build_graph(reprocess=False):
    retrieve_graph_edges(reprocess)
    save_graph_in_db()
