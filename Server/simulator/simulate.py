"""Simulator — creates ~100 fake users with distinct play styles and plays real
games through Server.db's save_result, populating the DB with realistic stats.
Usage: python simulator/simulate.py"""
import math
import os
import random
import sys
from collections import Counter

import psycopg
import wordfreq
from faker import Faker

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
import Client.wordl as wordl
from Server.admin.auth import hash_password
from Server.db import connect_db, save_result

NUM_USERS         = 100
SKILLED_FRACTION  = 1 / 3
SECONDS_PER_GUESS = (4, 30)
GAME_MIN = 12
GAME_MAX = 100
if len(sys.argv) > 1:
    NUM_USERS = int(sys.argv[1])
    if len(sys.argv) > 3:
        GAME_MIN = int(sys.argv[2])
        GAME_MAX = int(sys.argv[3])

def filter_candidates(candidates: list, guess: str, score: list) -> list:
    '''keeps only the candidates consistent with the score a guess produced, reusing
    wordl.score_guess as the single source of truth for scoring so this is hard-mode
    compliant by construction'''
    return [c for c in candidates if wordl.score_guess(guess, c) == score]


def pick_unskilled_guess(candidates: list) -> str:
    '''picks the most word-frequency-common remaining candidate'''
    return max(candidates, key=lambda w: wordfreq.zipf_frequency(w, "en"))


def entropy_for_guess(guess: str, candidates: list) -> float:
    '''expected information (bits) gained by guessing this word against the remaining candidates'''
    buckets = Counter(tuple(wordl.score_guess(guess, t)) for t in candidates)
    n = len(candidates)
    return -sum((c / n) * math.log2(c / n) for c in buckets.values())


def pick_skilled_guess(candidates: list) -> str:
    '''picks the candidate that maximizes expected information gain'''
    return max(candidates, key=lambda g: entropy_for_guess(g, candidates))


def generate_users(n: int = NUM_USERS) -> list:
    '''creates n fake user profiles: 1/3 skilled, each with a favorite starting word
    and a random per-game probability of opening with it'''
    fake = Faker()
    skilled_flags = [True] * (n // 3) + [False] * (n - n // 3)
    random.shuffle(skilled_flags)
    users = []
    for i in range(n):
        password_plain = fake.password(length=12)
        users.append({
            "username":       fake.unique.user_name(),
            "password_plain": password_plain,
            "password_hash":  hash_password(password_plain),
            "favorite_word":  random.choice(wordl.ANSWERS),
            "favorite_pct":   random.random(),
            "skilled":        skilled_flags[i],
        })
    return users


def insert_users(conn, users: list) -> list:
    '''bulk-creates users directly (login_or_register is interactive-only), retrying
    with a numeric suffix on a username collision against an already-populated DB'''
    with conn.cursor() as cur:
        for u in users:
            username = u["username"]
            for _ in range(5):
                try:
                    cur.execute(
                        "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                        (username, u["password_hash"]),
                    )
                    u["id"], u["username"] = cur.fetchone()[0], username
                    conn.commit()
                    break
                except psycopg.errors.UniqueViolation:
                    conn.rollback()
                    username = f"{u['username']}{random.randint(100, 999)}"
            else:
                raise RuntimeError(f"could not insert unique username for {u['username']}")
    return users


def play_game(conn, user: dict, first_skilled_guess: str) -> bool:
    '''plays one game for a user and records it via Server.db.save_result, returns whether they won'''
    target     = random.choice(wordl.ANSWERS)
    candidates = list(wordl.ANSWERS)
    guesses    = []
    won        = False

    for attempt in range(6):
        if attempt == 0 and random.random() < user["favorite_pct"]:
            guess = user["favorite_word"]
        elif user["skilled"]:
            guess = (first_skilled_guess if attempt == 0 and len(candidates) == len(wordl.ANSWERS)
                     else pick_skilled_guess(candidates))
        else:
            guess = pick_unskilled_guess(candidates)

        score = wordl.score_guess(guess, target)
        guesses.append(guess)
        if all(s == "green" for s in score):
            won = True
            break
        candidates = filter_candidates(candidates, guess, score)

    time_played = sum(random.randint(*SECONDS_PER_GUESS) for _ in guesses)
    save_result(conn, user["id"], target, guesses[0], len(guesses), won, time_played)
    return won


def main() -> None:
    game_range = (GAME_MIN, GAME_MAX)

    conn  = connect_db()
    users = insert_users(conn, generate_users())

    first_skilled_guess = pick_skilled_guess(wordl.ANSWERS) if any(u["skilled"] for u in users) else None

    total_games = 0
    for u in users:
        for _ in range(random.randint(*game_range)):
            play_game(conn, u, first_skilled_guess)
            total_games += 1
    conn.close()

    skilled_n = sum(u["skilled"] for u in users)
    print(f"Created {len(users)} users ({skilled_n} skilled / {len(users) - skilled_n} unskilled), "
          f"played {total_games} games.", file=sys.stderr)



if __name__ == "__main__":
    main()
