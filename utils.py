import csv
import os
import json
from pathlib import Path

data_location = Path('data')

def read_json(input_path):
    with open(input_path) as f:
        return json.load(f)

def read_tsv(input_path, with_header=True, delimiter='\t'):
    results = []
    with open(input_path) as f:
        if with_header:
            reader = csv.DictReader(f, delimiter='\t')
        else:
            reader = csv.reader(f, delimiter='\t')
        for row in reader:
            results.append(row)
    return results

def write_json_with_path(content, path, filename):
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(path / filename, 'w') as f:
        json.dump(content, f, indent=2)

def write_file_with_path(content, path, filename):
    if not os.path.isdir(path):
        os.makedirs(path)
    with open(path / filename, 'w') as f:
        f.write(content)
