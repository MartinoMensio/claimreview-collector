#!/usr/bin/env python

import csv
import itertools

from .. import utils
from .. import claimreview

subfolder_path = utils.data_location / "mrisdal_fakenews"


def main():
    data = utils.read_tsv(subfolder_path / "source" / "fake.csv", delimiter=",")

    # set([el['type'] for el in data])
    by_type_fn = lambda el: el["type"]
    cnt_by_type = {
        k: len(list(v))
        for k, v in itertools.groupby(sorted(data, key=by_type_fn), key=by_type_fn)
    }
    print("types", cnt_by_type)

    by_site_fn = lambda el: el["site_url"]
    types_by_domain = {
        k: set([el["type"] for el in v])
        for k, v in itertools.groupby(sorted(data, key=by_site_fn), key=by_site_fn)
    }

    result = []
    for k, v in types_by_domain.items():
        assert len(v) == 1
        label = v.pop()
        label = claimreview.simplify_label(label)
        if label:
            result.append({"domain": k, "label": label, "source": "mrisdal_fakenews"})

    utils.write_json_with_path(result, subfolder_path, "domains.json")
