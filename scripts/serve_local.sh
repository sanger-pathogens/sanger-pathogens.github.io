#!/bin/bash

set -eu
PORT=${1-8080}
cd $(dirname ${BASH_SOURCE[0]}) && cd ../site

echo "About to serve $(pwd) on port 127.0.0.1:$PORT"
python3 -m http.server --bind 127.0.0.1 $PORT
