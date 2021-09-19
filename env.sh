#!/usr/bin/env bash
set -eu
export VIRTUAL_ENV="$PWD/.env"
export PATH="$VIRTUAL_ENV/bin:${PATH-}"
exec "$@"
