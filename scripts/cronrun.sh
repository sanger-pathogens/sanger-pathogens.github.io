#!/bin/bash

set -eu

# This is a bit of a hack, you probably shouldn't be using it.
# The user which runs our cron jobs can't make changes to the
# directory where this is installed.  This project relies on
# making changes to this repo, committing them and then pushing
# them to Github.  The quickest solution I've come up with is to
# add this script which clones a new copy of the repo somewhere
# that this user can write to and then run the update from there.

# Sorry :(

logecho() {
  echo "[$(date "+%F %T")] INFO: $@"
}

cleanUp() {
  logecho "Cleaning up temporary directories"
  rm -rf "$tmp_checkout_dir" || True
}

tmp_checkout_dir=$(mktemp -d -t tmp_sanger-pathogens.github.io)
trap cleanUp EXIT

root_dir=$(cd $(dirname ${BASH_SOURCE}[0]) && cd .. && pwd)
cd $root_dir
remote_repo_url=$(git remote -v | awk '$1 == "origin" && $3 ~ /fetch/ {print $2}')

logecho "Cloning $remote_repo_url into $tmp_checkout_dir"
git clone --branch code $remote_repo_url $tmp_checkout_dir
cp "$root_dir/config.yml" "$tmp_checkout_dir/config.yml"
cd $tmp_checkout_dir
./scripts/blind_update.sh

trap - EXIT && cleanUp
