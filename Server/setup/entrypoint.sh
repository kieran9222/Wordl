#!/bin/sh
set -e

# cron jobs start with a minimal environment — bridge in the vars docker-compose
# injected at container start so the cron job can see POSTGRES_*/DB_* vars.
printenv | grep -E '^(POSTGRES_|DB_)' | sed 's/^/export /' > /etc/container.env

#starts the daily scheduler
cron
tail -F /var/log/cron.log &

#starts the python app so that it exits neatly when terminated
exec python3 /app/Server/main.py
