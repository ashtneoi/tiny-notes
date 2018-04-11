#!/usr/bin/env bash
set -eu

root="$(dirname "$0")/.."

if ! [[ -d "$root/.env" ]]; then
    virtualenv "$root/.env" -p "$(which python3)"
fi

source "$root/.env/bin/activate"
pip3 install bcrypt==3.1.3
