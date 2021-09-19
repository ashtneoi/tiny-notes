#!/usr/bin/env bash
set -eu

if ! [[ -d .env ]]; then
    python3 -mvenv .env
fi
source .env/bin/activate

pip3 install uWSGI==2.0.14 Werkzeug==0.11.15 toml==0.9.4
