# Organisation Summary

Creates a summary of an organisation's Github repos and
publishes it to github.io.

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-brightgreen.svg)](https://github.com/sanger-pathogens/sanger-pathogens.github.io/blob/code/licences/GPL-LICENSE)   
## Contents
  * [Introduction](#introduction)
  * [Usage (for sanger\-pathogens)](#usage-for-sanger-pathogens)
  * [Automated usage (for sanger\-pathogens)](#automated-usage-for-sanger-pathogens)
  * [Things to change (not for sanger\-pathogens)](#things-to-change-not-for-sanger-pathogens)
  * [License](#license)
  * [Feedback/Issues](#feedbackissues)

## Introduction

Github Pages serves static content from the `master` branch of
`<your-org-name>/<your-org-name>.github.io` on `https://<your-org-name>.github.io`.
In our case, this is [https://sanger-pathogens.github.io](https://sanger-pathogens.github.io).

## Usage (for sanger-pathogens)
Because `master` is served to the world, development in this repo is done on the `code` branch.

`update_repo_data.py` queries the Github API to get the latest data and 'score' each repo; this data is [stored in json](site/data/all.json).   
`update_pages.py` parses this data and uses a [template](templates/index.html) to create a [static html page](site/index.html).   
`serve_local.sh` can be used to serve a copy locally on port 8080.   
`deploy.sh` takes your local changes in the `site/` directory, copies the contents into a temporary copy of the `master` branch and then pushes them to the `master` branch on Github.   

You need to provide a username and api token to get the data from Github. This is entered in [config.yml](config.yml). If you're automating daily updates (via cron) then you probably also want to use an SSH key for Github. It's probably worth setting up a repo specific [deploy key](https://developer.github.com/guides/managing-deploy-keys/#deploy-keys) to reduce the impact if your key is compromised.   

- clone this repo
- create a [personal access token](https://github.com/settings/tokens)
- update [config.yml](config.yml)
- Run `update_repo_data.py` to download the latest data
- Run `update_pages.py` to update the html		
- Run `serve_local.py` to check your updates (see http://localhost:8080)
- Run `deploy.sh` to deploy your changes to github.io

## Automated usage (for sanger-pathogens)

- clone the repo using SSH onto a server
- create a [personal access token](https://github.com/settings/tokens)
- update [config.yml](config.yml)
- create a [deploy key](https://developer.github.com/guides/managing-deploy-keys/#deploy-keys) and install it on the server (without a password)
- create a cron job to run [cronrun.sh](./scripts/cronrun.sh)

Because we're automatically making and pushing commits, these scripts will only delete and modify files already known to Github to reduce the risk of a sensitive file being distributed to the world.  If you want to start serving a new file, you will need to manually push it to the `master` branch on the first occasion.   

`cronrun.sh` is a script we need to use because of potential file permissions incompatibility between the user we run the cron job with and the location our software is installed in. Other teams probably just need to use [blind_update.sh](scripts/blind_update.sh) instead.

## Things to change (not for sanger-pathogens)
- fork the repo
- clone and checkout the code branch `git clone --branch code <URL>`
- Update the following files:
  - [the config](config.yml)
  - [default config](config/)
  - [the template](templates/index.html)
  - [the logo](site/assets/img/logo.png)
  - [the favicon](site/favicon.ico)
- delete the master branch `git branch -D master`
- create a new master branch `git subtree split --prefix site -b master`
- force push to master (danger!) `git push -f origin master`
- rename the repo to `<your-org-name-here>.github.io`

NB Your pages won't be available after you fork; you need to actually push some changes to `master` before they're browsable.

## License
- The scripts, config and templates are licenced under [GPLv3](https://github.com/sanger-pathogens/sanger-pathogens.github.io/blob/code/licences/GPL-LICENSE).
- All rights are reserved for the images including the Wellcome Trust Sanger Institute logo. Please don't use them unless otherwise authorised to do so.
- The distinct CSS and Javascript libraries are licenced under their respective licences. Please review the source for details.

## Feedback/Issues
Please report any issues to path-help@sanger.ac.uk.
