# Wordl server
Server tools for the Wordl game. Runs Flask applications and a Postgres database to allow users to connect and play Wordl. Stores game and player history, automatically manages login streaks, runs a public leaderboard website and profile page, and can populate database with fake players.

## Requirements
Requires Python 3 and Docker. To install python dependencies, run
> pip install -r ./Server/requirements.txt

## Directions:
Enter the `Server/` directory. Set the Postgres server variables and exposed application port in `/.env` (see `/.env.example`.)

To start the server, run

> docker compose up -d

and wait for the container to start. The Postgres database is backed up on a volume on the disk, in a VM on Windows or Mac.

To take the server offline, pause it in the Docker desktop app, or run
> docker compose down

## Dashboard

Runs a web dashboard at http://localhost:[EXPOSED_PORT]/dashboard. For a local snapshot of the DB, run 
> py ./dashboard/dashboard.py

and open **dashboard.html**. `/dashboard/dashboard_app.py` runs the website as a Flask blueprint on the server, using functions from `/dashboard/dashboard.py` and HTML templates found in **/template/**

## Simulator

To populate the database with simulated users, see [`simulator/`](./simulator/README.md). The simulator requires the Wordl client to be available on the host machine, so `Client/` should not be removed.

## Other Processes
- Wordl clients connect to the server through a Flask blueprint in `/admin/game_server.py`, which updates the Postgres DB.
- Daily streaks are reset through `/scheduler/reset_daily_streak.py`, scheduled for every day at midnight UTC by **cron**.
- Flask blueprints are ran on the server by the main app in `/main.py`.
- `/db.py` and `/admin/auth.py` contain function required to connect to the database and to deal with user passwords respectively
- The Postgres database structure is defined in `/setup/migration.sql`
- The server container is defined in `/setup/Dockerfile`