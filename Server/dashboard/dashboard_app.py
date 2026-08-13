"""Server — Flask app serving the live dashboard: GET /dashboard (leaderboard,
profile search, popular starting words) and GET /dashboard/profile/<username>
(that player's stats, with a guesses-needed histogram that polls
/dashboard/profile/<username>/data every few seconds via Plotly.react, no
full page reload). Usage: python Server/dashboard/dashboard_app.py"""
import json
import os
import sys

from flask import Blueprint, Response, abort, jsonify

# allows for imports as Server.__
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Server.dashboard.dashboard import (
    build_guess_distribution_figure,
    build_index_context,
    fetch_guess_distribution,
    fetch_profile,
    render_page,
)
from Server.db import connect_db

GUESS_CHART_ID = "guesses-chart"
POLL_MILLIS    = 3000

welcometobpbrother = Blueprint("dashboard", __name__)


def _guess_chart_html(user_id: int) -> str:
    '''isn't in dashboard.py because that does not have profiles'''
    conn = connect_db()
    try:
        rows = fetch_guess_distribution(conn, user_id=user_id)
    finally:
        conn.close()
    fig = build_guess_distribution_figure(rows)
    return fig.to_html(full_html=False, include_plotlyjs="cdn", div_id=GUESS_CHART_ID)


@welcometobpbrother.route("/dashboard")
def dashboard_page():
    '''main dashboard: leaderboard, profile search, popular starting words'''
    conn = connect_db()
    try:
        context = build_index_context(conn)
    finally:
        conn.close()
    return Response(render_page("index.html", **context), mimetype="text/html")


@welcometobpbrother.route("/dashboard/profile/<username>")
def profile_page(username: str):
    '''a single player's stats, plus a live-updating guesses-needed histogram'''
    conn = connect_db()
    try:
        profile = fetch_profile(conn, username)
    finally:
        conn.close()

    if profile is None:
        return Response(
            render_page("profile.html", found=False, username=username),
            mimetype="text/html",
            status=404,
        )

    guess_chart_html = _guess_chart_html(profile["id"])
    return Response(
        render_page(
            "profile.html",
            found=True,
            username=username,
            profile=profile,
            guess_chart_html=guess_chart_html,
            poll_millis=POLL_MILLIS,
        ),
        mimetype="text/html",
    )


@welcometobpbrother.route("/dashboard/profile/<username>/data")
def profile_data(username: str):
    '''JSON the profile page polls to redraw the guesses histogram in place'''
    conn = connect_db()
    try:
        profile = fetch_profile(conn, username)
        if profile is None:
            abort(404)
        rows = fetch_guess_distribution(conn, user_id=profile["id"])
    finally:
        conn.close()
    fig = build_guess_distribution_figure(rows)
    return jsonify(json.loads(fig.to_json()))


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=False)
