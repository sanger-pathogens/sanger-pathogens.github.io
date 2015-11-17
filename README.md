# Organisation Summary

Creates a summary of an organisation's Github repos and
publishes it to github.io.

## Usage (by sanger-pathogens)

- clone this repo
- create a [personal access token](https://github.com/settings/tokens)
- update [config.yml](config.yml)
- Run `update_repo_data.py` to download the latest data
- Run `update_pages.py` to update the html		
- Run `serve_local.py` to check your updates
- Run `deploy.sh` to deploy your changes to github.io

## Automated usage (by sanger-pathogens)

- clone the repo using SSH onto a server
- create a [personal access token](https://github.com/settings/tokens)
- update [config.yml](config.yml)
- create a [deploy key](settings/keys) and install it on the server (without a password)
- create a cron job to run [blind_update.sh](./scripts/blind_update.sh)

## Things to change (not for sanger-pathogens)

- [the config](config.yml)
- [default config](config/)
- [the template](templates/index.html)
- [the logo](site/assets/img/logo.png)
- [the favicon](site/favicon.ico)

## Licences

- The scripts, config and templates are licenced under [GPLv3](licences/GPL-LICENCE)
- All rights are reserved for the images including the Wellcome Trust Sanger Institute logo.  Please don't use them unless otherwise authorised to do so.
- The distinct CSS and Javascript libraries are licenced under their respective licences.  Please review the source for details.
