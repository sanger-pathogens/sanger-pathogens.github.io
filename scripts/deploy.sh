#!/bin/bash

set -eu

# Deploys the contents of /site in the latest commit to
# origin/master so that it shows up in Github pages.

# NB this only updates files already tracked by origin/master
#    you need to make manual changes to deploy new files

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

# The following is all a bit horrible but, I think, necessary
# This will be run as part of a cron job and therefore should be
# somewhat robust.  We need to push changes to the master branch
# of the origin remote _but_ there are a couple of things that
# might make that hard.

# 1. Someone / thing else might have updated origin/master with
#    something incompatible
# 2. We only want to deploy changes to the site/ data and we
#    definitly don't want to accidentally pick up changes to
#    files which might contain tokens etc.


( git branch -D gh-pages 1>/dev/null 2>&1 && logecho "Deleting old (local) gh-pages branch" ) || True

logecho "Creating new gh-pages branch"
git subtree split --prefix site -b gh-pages 2>&1 | egrep -v '^-n '

original_branch=$(git rev-parse --abbrev-ref HEAD)
logecho "Changing from $original_branch to gh-pages"
git stash
git checkout gh-pages
last_local_commit=$(git log -1 --oneline | sed -E 's/[0-9a-z]{7}[ \t]+//')

logecho "Resetting gh-pages to origin/master"
git fetch origin 2>&1 > /dev/null
git reset origin/master

logecho "Re-adding changes to git"
for existing_file in $(git status --porcelain | awk '$1 ~ /M/ {print $2}'); do
  logecho "  adding \"$existing_file\""
  git add $existing_file
done
logecho "  commiting as \"$last_local_commit\""
git commit -m "$last_local_commit"

logecho "Pushing changes to origin/master"
git push origin gh-pages:master

logecho "Resetting back to \"$original_branch\""
git checkout $original_branch 2>&1 1>/dev/null
git stash pop
