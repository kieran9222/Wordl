import os
import sys

from flask import Blueprint, jsonify, request

#allows for imports as Server.__
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from Server.admin.auth import generate_token, hash_password, verify_password
from Server.db import connect_db, save_result

game_server = Blueprint('game_server', __name__)

# in-memory session store: token -> user_id. Lost on server restart (same
# tradeoff already accepted for the deletion-request design) — acceptable
# since a lost session just means logging in again.
SESSIONS: dict = {}


def require_token():
    '''looks up the Bearer token from the Authorization header, returns user_id or None'''
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    return SESSIONS.get(token)


@game_server.route("/login", methods=["POST"])
def login():
    '''checks credentials, returns token'''
    data = request.get_json()
    username, password = data["username"], data["password"]

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        if not row:
            return jsonify({"error": "no_such_user"}), 404

        user_id, stored_pw = row
        if not verify_password(password, stored_pw):
            return jsonify({"error": "bad_password"}), 401

        with conn.cursor() as cur:
            cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()

    token = generate_token()
    SESSIONS[token] = user_id
    return jsonify({"token": token, "user_id": user_id}), 200


@game_server.route("/register", methods=["POST"])
def register():
    '''registers user and returns token for use'''
    data = request.get_json()
    username, password = data["username"], data["password"]

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return jsonify({"error": "username_taken"}), 409

        hashed = hash_password(password)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                (username, hashed),
            )
            user_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    token = generate_token()
    SESSIONS[token] = user_id
    return jsonify({"token": token, "user_id": user_id}), 201


@game_server.route("/results", methods=["POST"])
def results():
    '''stores results if token is balid'''
    user_id = require_token()
    if user_id is None:
        return jsonify({"error": "invalid_token"}), 401

    data = request.get_json()
    conn = connect_db()
    try:
        save_result(
            conn, user_id,
            data["target_word"], data["start_word"],
            data["guesses"], data["win"], data["time_played"],
        )
    finally:
        conn.close()
    return jsonify({}), 200
