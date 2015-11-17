#!/bin/bash

set -eu

logecho() {
  echo "[$(date "+%F %T")] INFO: $@"
}

root_dir=$(cd $(dirname ${BASH_SOURCE}[0]) && cd .. && pwd)
cd $root_dir

logecho "Updating the data from Github"
./scripts/update_repo_data.py

logecho "Updating the pages in the local site/"
./scripts/update_pages.py

logecho "Deploying the changes to Github"
./scripts/deploy.sh
