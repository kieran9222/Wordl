FROM python:3.13-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends cron \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY Server/setup/docker_requirements.txt Server/setup/docker_requirements.txt
RUN pip install --no-cache-dir -r Server/setup/docker_requirements.txt

COPY Server/db.py Server/db.py
COPY Server/admin/auth.py Server/admin/auth.py
COPY Server/main.py Server/main.py
COPY Server/dashboard/ Server/dashboard/
COPY Server/admin/game_server.py Server/admin/game_server.py
COPY Server/scheduler/ Server/scheduler/

COPY Server/setup/crontab /etc/cron.d/wordl-cron
RUN chmod 0644 /etc/cron.d/wordl-cron \
 && crontab /etc/cron.d/wordl-cron \
 && touch /var/log/cron.log

COPY Server/setup/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
