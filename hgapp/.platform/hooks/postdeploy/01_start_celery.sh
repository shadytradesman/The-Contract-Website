#!/usr/bin/env bash
set -ex
source /var/app/venv/*/bin/activate && cd /var/app/current/ && celery -A hgapp worker --beat -l info --detach
