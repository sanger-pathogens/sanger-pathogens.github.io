#!/usr/bin/env python3

import yaml
from yaml.scanner import ScannerError

class ConfigError(ValueError):
  pass

def get_orgname():
  try:
    with open('config.yml', 'r') as config_file:
      config = yaml.load(config_file)
    return config['github_organisation']
  except FileNotFoundError:
    raise ConfigError('Please make sure that "config.yml" exists')
  except ScannerError as e:
    raise ConfigError("Please make sure that \"config.yml\" is valid Yaml: \n%s" % e)
  except (TypeError, KeyError):
    raise ConfigError('Please make sure that "config.yml" contains the key "github_organisation"')

if __name__ == '__main__':
  org_name = get_orgname()
  github_data = get_github_data(org_name)
  add_scores(github_data)
  add_readmes(github_data[:3])

  config_data = get_config_data()
  
  data = merge(repo_data, config_data)
  write_data(data)
