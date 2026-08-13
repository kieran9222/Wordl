"""Server — shared DB connection helper: builds the Postgres DSN from
POSTGRES_USER/PASSWORD/DB env vars (loaded from Server/.env for host-run dev)
plus POSTGRES_HOST/POSTGRES_PORT, which default to localhost/5432 for host-run
dev but are overridden to the docker-compose service name (postgres) when run
inside the app container. Usage: from Server.db import connect_db"""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_DSN = (f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
          f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{os.environ['POSTGRES_DB']}")


def connect_db():
    '''connects to the database with DB_DSN string, returns connection'''
    return psycopg.connect(DB_DSN)


def save_result(conn, user_id: int, target_word: str, start_word: str,
                 guesses_count: int, won: bool, time_played: int) -> None:
    '''writes a row to the results table, then recalculates win_streak/total_wins/total_games on
    users from the results table so there's no drift'''
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO results (user_id, target_word, start_word, guesses, win, timer) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, target_word, start_word, guesses_count, won, time_played),
        )

        cur.execute(
            "SELECT count(*), count(*) FILTER (WHERE win) FROM results WHERE user_id = %s",
            (user_id,),
        )
        total_games, total_wins = cur.fetchone()

        cur.execute("SELECT win FROM results WHERE user_id = %s ORDER BY id DESC", (user_id,))
        win_streak = 0
        for (win,) in cur.fetchall():
            if not win:
                break
            win_streak += 1

        cur.execute(
            """UPDATE users
               SET win_streak = %s, total_wins = %s, total_games = %s,
                   longest_streak = GREATEST(longest_streak, %s)
               WHERE id = %s""",
            (win_streak, total_wins, total_games, win_streak, user_id),
        )
    conn.commit()
