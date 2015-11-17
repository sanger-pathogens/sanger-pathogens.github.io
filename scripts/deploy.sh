#!/bin/bash

set -eu

# Deploys the contents of /site in the latest commit to
# origin/master so that it shows up in Github pages.

logecho() {
  echo "[$(date "+%F %T")] INFO: $@"
}

cleanUp() {
  logecho "Error! cleaning up before exiting"
  if [ -e "$root_dir/tmp_repo" ]; then
    rm -rf "$root_dir/last_failure__tmp_repo" || True
    mv "$root_dir/tmp_repo" "$root_dir/last_failure__tmp_repo"
  fi
}

root_dir=$(cd $(dirname ${BASH_SOURCE}[0]) && cd .. && pwd)
cd $root_dir
remote_repo_url=$(git remote -v | awk '$1 == "origin" && $3 ~ /fetch/ {print $2}')
logecho "Remote repo is \"$remote_repo_url\""

logecho "Creating temporary copy of the remote repo"
trap cleanUp EXIT
git clone --branch master --no-checkout $remote_repo_url tmp_repo
cp -r site/* tmp_repo
cd tmp_repo
git reset HEAD . || True

logecho "Staging local changes"
for modified_file in $(git status --porcelain | awk '$1 == "M" {print $2}'); do
  logecho "  adding $modified_file"
  git add $modified_file
done
for modified_file in $(git status --porcelain | awk '$1 == "D" {print $2}'); do
  logecho "  deleting $modified_file"
  git rm $modified_file
done

logecho "Checking for awkward changes"
other_changes=$(git status --porcelain | awk '$1 !~ /^[MD]$/ {print $2}' | wc -l)
if [ 0 -ne "$other_changes" ]; then
  logecho "Error! There were some changes which can't be automated.  Please fix them manually"
  logecho "Changes:"
  git status --porcelain | awk '$1 !~ /^[MD]$/'
  exit 1
else
  logecho "  none found :)"
fi

logecho "Committing and pushing changes"
git commit -m "Automatic Update: $(date)"
git push origin master

logecho "Tidying up"
cd $root_dir
rm -rf tmp_repo
trap - EXIT # Don't want to try cleanUp when we exit happily
