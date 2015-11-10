#!/usr/bin/env python3

import datetime
import logging
import requests
import yaml

from requests.auth import HTTPBasicAuth
from yaml.scanner import ScannerError

class ConfigError(ValueError):
  pass

def get_github_config():
  logger.info("Loading Github config")
  try:
    with open('config.yml', 'r') as config_file:
      config = yaml.load(config_file)
    logger.info("Organisation is {github_organisation}, username is {username}".format(**config))
    return {key: config[key] for key in ['github_organisation', 'username',
                                          'token']}
  except FileNotFoundError:
    raise ConfigError('Please make sure that "config.yml" exists')
  except ScannerError as e:
    raise ConfigError("Please make sure that \"config.yml\" is valid Yaml: \n%s" % e)
  except (TypeError, KeyError):
    raise ConfigError('Please make sure that "config.yml" contains your github_organisation, username and authentication token')

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

def add_release_data(data, github_get):
  logger.info("Adding details of releases")
  for repo in data:
    logger.debug("Adding release data to %s", data['name'])
    release_url = repo['releases_url'][:-5] # remove '{/id}' suffix
    release_data = github_get(release_url).json()
    repo['release_count'] = len(release_data)
    def by_publish_date(release):
      publication_date = release['published_at']
      return datetime.datetime.strptime(publication_date, '%Y-%m-%dT%H:%M:%SZ')
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
  if username is None or token is None:
    return lambda url: requests.get(url)
  else:
    auth_token=HTTPBasicAuth(username, token)
    return lambda url: requests.get(url, auth=auth_token)

logger = logging.getLogger('sanger_pathogens.update_repo_data')

if __name__ == '__main__':
  logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s",
                      level=logging.DEBUG)

  github_config = get_github_config()
  github_get = create_http_getter(github_config['username'],
                                  github_config['token'])
  github_data = get_github_data(github_config['github_organisation'], github_get)
  add_scores(github_data)
  add_readmes(github_data[:3])

  config_data = get_config_data()
  
  data = merge(repo_data, config_data)
  write_data(data)
