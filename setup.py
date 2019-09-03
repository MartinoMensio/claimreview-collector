#!/usr/bin/env python

from setuptools import setup

setup(name='datasets',
      version='1.0',
      description='Dataset aggregation for MisinfoMe',
      author='AAA',
      author_email='a@a.a',
      url='https://a.a.a',
      packages=['datasets'],
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
          'pyld'
      ])
