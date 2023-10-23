#!/usr/bin/env bash
source /var/app/venv/*/bin/activate && cd /var/app/current/ && celery -A hgapp worker --beat -l info --detach
