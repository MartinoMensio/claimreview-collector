# coding: utf8

if __name__ == '__main__':
    import plac
    import sys

    from .cli import commands


    commands = {
        'process_all': commands.process_all,
        'aggregate_all': commands.aggregate_all,
        'scrape_factchecking': commands.scrape_factchecking,
        'scrape_single_factchecking': commands.scrape_single_factchecking,
        'process_factchecker_lists': commands.process_factchecker_lists,
        'process_single_factchecker_list': commands.process_single_factchecker_list,
        'process_datasets': commands.process_datasets,
        'process_single_dataset': commands.process_single_dataset,
        'retrieve_graph_edges': commands.retrieve_graph_edges,
        'save_graph_in_db': commands.save_graph_in_db,
        'build_graph': commands.build_graph
    }
    if len(sys.argv) == 1:
        print('Available commands:', ', '.join(commands))
        exit()
    command = sys.argv.pop(1)
    sys.argv[0] = 'spacy %s' % command
    if command in commands:
        plac.call(commands[command], sys.argv[1:])
    else:
        print("Unknown command: %s" % command, "Available: %s" % ', '.join(commands))