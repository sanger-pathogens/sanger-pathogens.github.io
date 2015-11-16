#!/bin/bash

set -eu

logecho() {
  echo "[$(date "+%F %T")] INFO: $@"
}

root_dir=$(cd $(dirname ${BASH_SOURCE}[0]) && cd .. && pwd)
cd $root_dir

changes=$(git status site/ --porcelain)
if [ ! -z "$changes" ]; then
  logecho "There are uncommited changes to site/; please commit or stash them"
  git status site/
  exit 1
fi

logecho "Updating the data from Github"
./scripts/update_repo_data.py

logecho "Updating the pages in the local site/"
./scripts/update_pages.py

for existing_file in $(git status site/ --porcelain | awk '$1 ~ /M/ {print $2}'); do
  logecho Adding "$existing_file" to git
  git add $existing_file
done

logecho "Creating new commit with changes"
git commit -m "Auto-update: $(date)"

logecho "Deploying the changes to Github"
./scripts/deploy.sh
