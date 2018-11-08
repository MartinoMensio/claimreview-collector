#!/bin/env python

import utils

dataset = 'datacommons_feeds'
input_file = utils.data_location / 'datacommons_feeds' / 'source' / 'data.json'

data = utils.read_json(input_file)

