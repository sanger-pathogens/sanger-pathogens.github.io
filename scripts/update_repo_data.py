#!/usr/bin/env python3

if __name__ == '__main__':
  org_name = get_orgname()
  github_data = get_github_data(org_name)
  add_scores(github_data)
  add_readmes(github_data[:3])

  config_data = get_config_data()
  
  data = merge(repo_data, config_data)
  write_data(data)
