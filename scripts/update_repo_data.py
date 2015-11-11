#!/usr/bin/env python3

import datetime
import logging
import re
import requests
import yaml

from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from yaml.scanner import ScannerError

class ConfigError(ValueError):
  pass

class GithubError(ValueError):
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
      'watchers_count',
      'url'
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
  for repo in data:
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

def inline_markdown_links(readme):
  link_lookup = re.compile('^\s*\[([^\]]+)\]:\s*(\S+)\s*$', re.M)
  link_details = {text: url for text, url in
                  re.findall(link_lookup, readme)}
  readme = re.sub(link_lookup, '', readme)
  link_link_lookup = '\[([^]]+)\]\s*\[([^]]+)\]'
  for text, link in re.findall(link_link_lookup, readme):
    if link in link_details:
      link_details[text] = link_details[link]
  readme = re.sub(link_link_lookup, r'[\1]', readme)
  for link_text, url in link_details.items():
    readme = re.sub("\[%s\]" % link_text, "[%s](%s)" % (link_text, url), readme)
  return readme

def summarise_markdown(readme):
  #logging.debug(">>>>>>>>>ORIGINAL:\n%s", readme[:1000])
  # remove travis
  readme = re.sub('\[!\[Build Status\]\(https://travis-ci.org/[^)]*\)\]\(https://travis-ci.org/[^)]*\)\n*',
                  '', readme)
  #logging.debug(">>>>>>>>>No TRAVIS:\n%s", readme[:1000])
  # fix links
  readme = inline_markdown_links(readme)
  #logging.debug(">>>>>>>>>No empty:\n%s", readme[:1000])
  # remove code snippets
  readme = re.sub(re.compile('```.+```', re.S), '', readme) # multiline scripts
  # remove empty lines
  readme = re.sub(re.compile('\n+', re.M), '\n', readme)
  #logging.debug(">>>>>>>>>No Code:\n%s", readme[:1000])
  # remove a heading if it's the first thing in the readme
  underlined_heading = '[^\n]+\n[=-]+\n?'
  hash_heading = '#+\s*.+'
  m = re.match('^' + underlined_heading, readme)
  if m and m.start() == 0:
    readme = re.sub('^' + underlined_heading, '', readme)
  else:
    m = re.match('^' + hash_heading + '$', readme)
    if m and m.start() == 0:
      readme = re.sub('^' + hash_heading + '$', '', readme)
  #logging.debug(">>>>>>>>>First heading:\n%s", readme[:1000])
  # Remove from the next heading thing
  readme = re.sub(re.compile(underlined_heading + '.+', re.S), '', readme)
  readme = re.sub(re.compile(hash_heading, re.S), '', readme)
  #logging.debug(">>>>>>>>>Output:")
  # remove empty lines
  readme = re.sub(re.compile('^\n+', re.M), '', readme)
  return readme

def add_readmes(data, github_get):
  logger.info("Adding Readme data")
  for repo in data:
    logger.debug("Adding Readme data for %s" % repo['name'])
    readme_url = repo['url'] + '/readme'
    try:
      readme_data = github_get(readme_url).json()
    except HTTPError as e:
      if e.response.status_code == 404:
        repo['readme_content'] = None
        repo['readme_name'] = None
        continue # doesn't have a readme
      else:
        raise
    base64_content = readme_data['content'].replace('\n', '')
    readme_content = base64.b64decode(base64_content).decode('utf8')
    readme_name = readme_data['name']
    repo['readme_content'] = readme_content
    repo['readme_name'] = readme_name

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
