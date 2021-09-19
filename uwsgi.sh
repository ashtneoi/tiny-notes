#!/usr/bin/env bash
set -eu
PORT="$1"
shift
./env.sh uwsgi --http-socket="127.0.0.1:$PORT" --wsgi-file=main.py "$@"
