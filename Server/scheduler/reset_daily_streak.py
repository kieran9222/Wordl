"""Scheduler — resets daily_login_streak to 0 for any user with no login on the
day that just ended, run once daily via cron shortly after midnight.
Usage: python Server/scheduler/reset_daily_streak.py"""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Server.db import connect_db


def reset_daily_streaks(conn) -> int:
    '''resets daily_login_streak to 0 for users with no login anywhere on the day
    that just ended (checking against CURRENT_DATE alone would incorrectly reset
    everyone, since the new day starts with zero logins from anyone by definition)'''
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET daily_login_streak = 0 WHERE last_login < CURRENT_DATE - INTERVAL '1 day'")
        updated = cur.rowcount
    conn.commit()
    return updated


def main() -> None:
    conn = connect_db()
    try:
        updated = reset_daily_streaks(conn)
    finally:
        conn.close()
    print(f"Reset daily_login_streak for {updated} user(s).")


if __name__ == "__main__":
    main()
