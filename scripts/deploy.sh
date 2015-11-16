#!/bin/bash

set -eux

read_config() {
  cat config.yml | python3 -c "import yaml, sys; print(yaml.load(sys.stdin)['$1'])"
}


root_dir=$(cd $(dirname ${BASH_SOURCE}[0]) && cd .. && pwd)
cd $root_dir
username=$(read_config username)
token=$(read_config token)
deploy_repo=$(read_config deploy_repo)
deploy_user_email=$(read_config deploy_user_email)

echo $username $token $deploy_repo $deploy_user_email

#mkdir tmp_site && cd tmp_site
#git clone -b master "https://github.com/${deploy_repo}.git"
#cd $deploy_repo
#git config user.name "$username autodeploy"
#git config user.email $deploy_user_email
#ls -a $deploy_repo | grep -v '.git' | xargs -I FILE rm	 -rf "${deploy_repo}/FILE"
#cp -r ../../site/* .
#git add .
#git commit -m "Autodeploy by $username @ $(date)"
#git push "https://${token}@github.com/${deploy_repo}.git" master
#cd ../../
#rm -r tmp_site
