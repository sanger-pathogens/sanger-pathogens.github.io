#!/usr/bin/env python3

import logging
import os

from jinja2 import Environment, FileSystemLoader

def get_loader():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  parent_dir = os.path.dirname(script_dir)
  templates_dir = os.path.join(parent_dir, 'templates')
  logger.debug("Loading templates from '%s'" % templates_dir)
  return FileSystemLoader(templates_dir)

def site_dir():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  parent_dir = os.path.dirname(script_dir)
  return os.path.join(parent_dir, 'site')

logger = logging.getLogger('sanger_pathogens.update_pages')

if __name__ == '__main__':
  logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s",
                      level=logging.DEBUG)
  env = Environment(loader=get_loader())
  index_template = env.get_template('index.html')
  index_path = os.path.join(site_dir(), 'index.html')
  with open(index_path, 'w') as index_file:
    print(index_template.render(who='world!'), file=index_file)
