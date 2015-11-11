#!/usr/bin/env python3

import json
import logging
import os

from jinja2 import Environment, FileSystemLoader

def parent_dir():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  return os.path.dirname(script_dir)

def get_loader():
  templates_dir = os.path.join(parent_dir(), 'templates')
  logger.debug("Loading templates from '%s'" % templates_dir)
  return FileSystemLoader(templates_dir)

def site_dir():
  return os.path.join(parent_dir(), 'site')

def get_data():
  data_path = os.path.join(site_dir(), 'data', 'all.json')
  with open(data_path, 'r') as data_file:
    logging.debug("Getting data from '%s'" % data_path)
    data = json.load(data_file)
  return data

logger = logging.getLogger('sanger_pathogens.update_pages')

if __name__ == '__main__':
  logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s",
                      level=logging.DEBUG)
  env = Environment(loader=get_loader())
  index_template = env.get_template('index.html')
  index_path = os.path.join(site_dir(), 'index.html')
  data = get_data()
  repos = data['repos']
  repos = sorted(repos, key=lambda r: r['score'], reverse=True)
  featured_repos = repos[:3]
  other_repos = repos[3:]
  name = data['name']
  organisation_name = data['organisation_name']
  collected_at = data['collected_at']
  with open(index_path, 'w') as index_file:
    print(index_template.render(featured_repos=featured_repos,
                                other_repos=other_repos,
                                name=name,
                                organisation_name=organisation_name,
                                collected_at=collected_at),
          file=index_file)
