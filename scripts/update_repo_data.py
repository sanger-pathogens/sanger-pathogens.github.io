#!/usr/bin/env python3

import datetime
import json
import logging
import math
import os
import requests
import yaml

from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from yaml.scanner import ScannerError

class ConfigError(ValueError):
  pass

class GithubError(ValueError):
  pass

def script_directory():
  script_path = os.path.realpath(__file__)
  return os.path.dirname(script_path)

def get_github_config():
  logger.info("Loading Github config")
  try:
    parent_dir = os.path.dirname(script_directory())
    config_file = os.path.join(parent_dir, 'config.yml')
    with open(config_file, 'r') as config_file:
      config = yaml.load(config_file)
    logger.info("Organisation is {github_organisation}, username is {username}".format(**config))
    return {key: config[key] for key in ['github_organisation', 'username',
                                          'token']}
  except FileNotFoundError:
    raise ConfigError("Please make sure that \"%s\" exists" % config_file)
  except ScannerError as e:
    raise ConfigError("Please make sure that \"%s\" is valid Yaml: \n%s" %
                      (config_file, e))
  except (TypeError, KeyError):
    raise ConfigError("Please make sure that \"%s\" contains your github_organisation, username and authentication token" %
                     config_file)

def deduplicate_github_data(data):
  # There's a small chance of duplication due
  # to pagination.  Lets be carefull
  logger.debug("Removing duplicate repos from data")
  data_dict = {el['name']: el for el in data}
  return list(data_dict.values())

def discard_some_data(data):
  logger.debug("Removing unnecessary repo details")
  def data_to_keep(repo):
    keys_to_keep = [
      'name',
      'description',
      'homepage',
      'html_url',
      'forks',
      'language',
      'pushed_at',
      'stargazers_count',
      'releases_url',
      'watchers_count'
    ]
    return {key: repo[key] for key in keys_to_keep}
  return [data_to_keep(repo) for repo in data]

def parse_time(t):
  return datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')

def add_release_data(data, github_get):
  logger.info("Adding details of releases")
  for repo in data:
    logger.debug("Adding release data to %s", repo['name'])
    release_url = repo['releases_url'][:-5] # remove '{/id}' suffix
    release_data = github_get(release_url).json()
    repo['release_count'] = len(release_data)
    def by_publish_date(release):
      publication_date = release['published_at']
      return parse_time(publication_date)
    if repo['release_count'] > 0:
      latest_release = max(release_data, key=by_publish_date)
      repo['release_version'] = latest_release['tag_name']
      repo['release_date'] = latest_release['published_at']

def get_github_data(org_name, github_get):
  logger.info("Getting data from Github for %s", org_name)
  data = []
  next_page = "https://api.github.com/orgs/%s/repos?page=1" % org_name
  for i in range(100):
    response = github_get(next_page)
    data += response.json()
    try:
      next_page = response.links['next']['url']
    except KeyError:
      break # There aren't more pages
  data = deduplicate_github_data(data)
  data = discard_some_data(data)
  add_release_data(data, github_get)
  return data

def create_http_getter(username=None, token=None):
  def get(url):
    if username is None or token is None:
      response = requests.get(url)
    else:
      auth_token=HTTPBasicAuth(username, token)
      response = requests.get(url, auth=auth_token)
    try:
      response.raise_for_status()
      return response
    except HTTPError as e:
      if e.response.status_code == 403:
        logger.exception("Not allowed to access %s; you're probably being rate limited" % url)
      else:
        raise
  return get

def decay(t, half_life, now=None):
  # decay(now() - timedelta(days=14), timedelta(days=7), now()) == 0.25
  if now is None:
    now = datetime.datetime.now()
  return math.e ** (-(now-t).total_seconds() * math.log(2) / half_life.total_seconds())

def tend_to(count, half_count):
  # tend_to(0, 1) == 0.0
  # tend_to(1, 1) == 0.5
  # tend_to(2, 1) == 0.75
  # tend_to(3, 1) == 0.875
  # tend_to(-1, 1) == 0.0
  if count == None or count < 0:
    return 0
  return 1 - (math.e ** (-count * math.log(2) / half_count))

def add_scores(data):
  logging.info("Scoring repos")
  for repo in data:
    logging.debug("Scoring '%s'" % repo['name'])
    score = 0
    score += 1 if len(repo['description']) > 0 else 0
    score += 1 if repo['homepage'] is not None else 0
    pushed_at = parse_time(repo['pushed_at'])
    score += 1 * decay(pushed_at, datetime.timedelta(days=7))
    score += 1 * tend_to(repo['release_count'], 3)
    try:
      last_release = parse_time(repo['release_date'])
      score += 1 * decay(last_release, datetime.timedelta(days=7))
    except KeyError:
      pass # No releases
    score += 1 * tend_to(repo['stargazers_count'], 3)
    repo['score'] = score

def get_config_data():
  parent_dir = os.path.dirname(script_directory())
  config_dir = os.path.join(parent_dir, 'config')
  files = [os.path.join(config_dir, f) for f in os.listdir(config_dir) if
           os.path.isfile(os.path.join(config_dir, f))]
  config_files = {os.path.basename(f)[:-4]: f for f in files if f[-4:] == '.yml'}
  logging.info("Loading config from %s files in '%s'" % (len(config_files),
                                                         config_dir))
  config = []
  for name, file_path in config_files.items():
    with open(file_path, 'r') as config_file:
      logging.debug("Loading config from '%s' (%s)" % (file_path, name))
      new_config = yaml.load(config_file)
      new_config['name'] = name
      config.append(new_config)
  return config

def merge(repo_data, config_data):
  logging.info("Merging data from Github and config files")
  repo_data = {repo['name']: repo for repo in repo_data}
  config_data = {config['name']: config for config in config_data}
  for name, repo in repo_data.items():
    repo.update(config_data.get(name, {}))
  for name, repo in config_data.items():
    if name not in repo_data:
      repo_data[name] = repo
  for repo in repo_data.values():
    multiplier = repo.get('score_multiplier', 1)
    repo['moderated_score'] = repo['score'] * multiplier
  return list(repo_data.values())

def write_data(data):
  parent_dir = os.path.dirname(script_directory())
  data_path = os.path.join(parent_dir, 'site', 'data', 'all.json')
  with open(data_path, 'w') as data_file:
    logging.info("Writing details of %s repos to '%s'" % (len(data), data_path))
    sorted_data = sorted(data, key=lambda r: r['score'], reverse=True)
    json.dump({'data': sorted_data}, data_file, sort_keys=True,
              indent=2, separators=(',', ': '))

logger = logging.getLogger('sanger_pathogens.update_repo_data')

if __name__ == '__main__':
  logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s",
                      level=logging.DEBUG)

  github_config = get_github_config()
  github_get = create_http_getter(github_config['username'],
                                  github_config['token'])
  github_data = get_github_data(github_config['github_organisation'], github_get)
  add_scores(github_data)

  config_data = get_config_data()
  
  data = merge(github_data, config_data)
  write_data(data)
