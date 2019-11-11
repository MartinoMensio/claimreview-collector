# this is the main API for the module as a dependency

import os
from dotenv import load_dotenv
from pathlib import Path
from .cli import commands
from .processing import utils

# sets up the library
utils.set_data_location('tmp')
local_env_file = Path(os.path.dirname(os.path.realpath(__file__))) / '..' / '.env'
if not os.environ.get('GOOGLE_FACTCHECK_EXPLORER_COOKIE'):
    load_dotenv(local_env_file)

print(os.environ.get('ESI_USER'))
print(os.environ.get('ESI_PASS'))
print(os.environ.get('GOOGLE_FACTCHECK_EXPLORER_COOKIE'))

def update_claimreviews():
    commands.scrape_factchecking()
    commands.aggregate_all()
