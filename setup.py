#!/usr/bin/env python

from setuptools import setup

setup(name='claimreview_scraper',
      version='1.0',
      description='ClaimReview Scraper for MisinfoMe',
      author='Martino Mensio',
      author_email='martino.mensio@open.ac.uk',
      url='https://a.a.a',
      packages=['claimreview_scraper'],
      python_requires='>=3',
      install_requires=[
          'extruct',
          'pylint',
          'requests',
          'tqdm',
          'plac',
          'flatten_json',
          'python-dotenv',
          'pymongo',
          'validators',
          'tldextract',
          'beautifulsoup4',
          'dateparser',
          'unidecode',
          'pycountry',
          'dirtyjson',
          'rdflib-jsonld',
          'pyld',
          'scipy',
          'jellyfish',
          'pandas'
      ])
