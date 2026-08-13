"""Dashboard — queries the live DB and renders the dashboard pages: a main
page (leaderboard, profile search, popular starting words) and per-user
profile pages (win/loss totals, favorite starting word, streaks, last login,
guesses-needed histogram). Usage: python dashboard/dashboard.py writes a
static snapshot of the main page to dashboard.html."""
import os
import sys

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape

OUTPUT_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Validated default palette (see .claude dataviz skill) — colors assigned by job,
# not picked for looks: BLUE for single-series magnitude, GOOD/CRITICAL (the
# reserved status pair) for win/loss since that's a state, not just a category.
SURFACE   = "#fcfcfb"
PAGE      = "#f9f9f7"
INK       = "#0b0b0b"
SECONDARY = "#52514e"
MUTED     = "#898781"
GRIDLINE  = "#e1e0d9"
BASELINE  = "#c3c2b7"
BLUE      = "#2a78d6"
GOOD      = "#0ca30c"
CRITICAL  = "#d03b3b"

LAYOUT_BASE = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK),
    margin=dict(l=60, r=30, t=50, b=50),
)

_JINJA_ENV = Environment(
    loader=FileSystemLoader(TEMPLATES_PATH),
    autoescape=select_autoescape(["html"]),
)


def render_page(template_name: str, **context) -> str:
    '''renders one of the templates in templates/ with the given context'''
    return _JINJA_ENV.get_template(template_name).render(**context)


'''Data acquiring functions, using cursor as context'''

_LEADERBOARD_COLUMNS = {"wins": "total_wins", "streak": "longest_streak"}


def fetch_leaderboard(conn, sort: str = "wins", limit: int = 10) -> list:
    column = _LEADERBOARD_COLUMNS.get(sort, "total_wins")
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT username, {column} FROM users ORDER BY {column} DESC, username LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def fetch_popular_words(conn, limit: int = 10) -> list:
    '''most-played starting words with their win rate'''
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT start_word,
                   count(*) AS plays,
                   count(*) FILTER (WHERE win) AS wins
            FROM results
            GROUP BY start_word
            ORDER BY plays DESC, start_word
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def fetch_usernames(conn) -> list:
    '''all usernames, for the profile-search datalist'''
    with conn.cursor() as cur:
        cur.execute("SELECT username FROM users ORDER BY username")
        return [row[0] for row in cur.fetchall()]


def fetch_profile(conn, username: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, username, total_wins, total_games, win_streak,
                   longest_streak, last_login
            FROM users WHERE username = %s
            """,
            (username,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    user_id = row[0]
    return {
        "id": user_id,
        "username": row[1],
        "total_wins": row[2],
        "total_games": row[3],
        "total_losses": row[3] - row[2],
        "win_streak": row[4],
        "longest_streak": row[5],
        "last_login": row[6],
        "favorite_word": fetch_favorite_word(conn, user_id),
    }


def fetch_favorite_word(conn, user_id: int) -> str | None:
    '''the starting word this user has opened with the most'''
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT start_word FROM results WHERE user_id = %s
            GROUP BY start_word ORDER BY count(*) DESC, start_word LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return row[0] if row else None


def fetch_guess_distribution(conn, user_id: int | None = None) -> list:
    '''uses group by to count the number of games in each guess'''
    with conn.cursor() as cur:
        if user_id is None:
            cur.execute(
                "SELECT guesses, count(*) FROM results WHERE win = TRUE GROUP BY guesses ORDER BY guesses"
            )
        else:
            cur.execute(
                """
                SELECT guesses, count(*) FROM results
                WHERE win = TRUE AND user_id = %s
                GROUP BY guesses ORDER BY guesses
                """,
                (user_id,),
            )
        return cur.fetchall()


'''builds plotly graphs'''


def build_guess_distribution_figure(rows: list) -> go.Figure:
    '''always plots all 6 by defaulting counts to 0 when guesses arent there, gets rows from fetch_guess_distribution'''
    counts_by_guess = dict(rows)
    guesses = [str(g) for g in range(1, 7)]
    counts  = [counts_by_guess.get(g, 0) for g in range(1, 7)]
    fig = go.Figure(go.Bar(
        x=guesses, y=counts, marker_color=BLUE,
        hovertemplate="%{x} guesses: %{y} wins<extra></extra>",
    ))
    fig.update_layout(
        title="Guesses needed to win",
        xaxis=dict(title="Guesses", gridcolor=GRIDLINE, zerolinecolor=BASELINE),
        yaxis=dict(title="Games won", gridcolor=GRIDLINE, zerolinecolor=BASELINE),
        **LAYOUT_BASE,
    )
    return fig


def build_index_context(conn) -> dict:
    '''gathers everything the main dashboard page needs'''
    return {
        "leaderboards": {
            "wins": fetch_leaderboard(conn, sort="wins"),
            "streak": fetch_leaderboard(conn, sort="streak"),
        },
        "popular_words": fetch_popular_words(conn),
        "usernames": fetch_usernames(conn),
    }


def main() -> None:
    '''used to build a static snapshot of the main page instead of serving it up on Flask'''
    _PARENT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _PARENT not in sys.path:
        sys.path.insert(0, _PARENT)
    from Server.db import connect_db

    conn = connect_db()
    context = build_index_context(conn)
    conn.close()

    html = render_page("index.html", **context)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
