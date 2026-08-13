"""Wordl — a terminal Wordle clone. Usage: python wordl.py"""
import os
import random
import sys
import time

import requests
from dotenv import load_dotenv

# ── ANSI constants ────────────────────────────────────────────────────────────
RESET     = "\033[0m"
BOLD      = "\033[1m"
BG_GREEN  = "\033[42m"
BG_YELLOW = "\033[43m"
BG_GRAY   = "\033[100m"
BG_EMPTY  = "\033[47m"
FG_WHITE  = "\033[97m"
FG_BLACK  = "\033[30m"

STATUS_COLORS = {
    "green":  (BG_GREEN,  FG_WHITE),
    "yellow": (BG_YELLOW, FG_WHITE),
    "gray":   (BG_GRAY,   FG_WHITE),
    "empty":  (BG_EMPTY,  FG_BLACK),
}

KEYBOARD_FG = {
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "gray":    "\033[90m",
    "unknown": "\033[37m",
}

STATUS_PRIORITY = {"green": 3, "yellow": 2, "gray": 1, "unknown": 0}
KEYBOARD_ROWS   = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]

# ── Word lists ────────────────────────────────────────────────────────────────
def _load_words(path: str) -> list:
    '''Returns a list of the 5-letter words from a file, used for the answers and guesses'''
    with open(path, encoding="utf-8") as f:
        return [w for line in f if len(w := line.strip().lower()) == 5 and w.isalpha()]

_DIR          = os.path.dirname(os.path.abspath(__file__))
ANSWERS       = _load_words(os.path.join(_DIR, "data/answers.txt"))
_ALL_GUESSES  = _load_words(os.path.join(_DIR, "data/words.txt"))
ALL_WORDS     = set(_ALL_GUESSES) | set(ANSWERS)

load_dotenv()
GAME_SERVER_URL = os.environ["GAME_SERVER_URL"]


def _call_game_server(path: str, json: dict):
    '''POSTs to the game server, exiting cleanly (rather than a raw traceback) if it's unreachable —
    unlike a failed result-save, a failed login/register truly blocks play'''
    try:
        return requests.post(f"{GAME_SERVER_URL}{path}", json=json)
    except requests.exceptions.RequestException:
        print("  Can't reach the game server right now.")
        sys.exit(1)


def login_or_register() -> tuple:
    '''single function to handle login screen. Works recursively until it can return a valid user ID,
    creating a user if it has to'''
    print("\n  ── Account ───────────────────────────────")
    print("  [1] Login")
    print("  [2] Create account")
    while True:
        choice = input("  > ").strip()
        if choice in ("1", "2"):
            break
        print("  Please enter 1 or 2.")

    username = input("  Username: ").strip()

    if choice == "1":
        while True:
            password = input("  Password: ").strip()
            resp = _call_game_server("/login", {"username": username, "password": password})
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Welcome back, {username}!")
                return data["user_id"], data["token"]
            if resp.status_code == 404:
                print(f"  No account found for '{username}'. Please try again.")
                return login_or_register()
            print("  Incorrect password, try again.")
    else:
        while True:
            password = input("  Password: ").strip()
            confirm  = input("  Confirm password: ").strip()
            if password == confirm:
                break
            print("  Passwords do not match, try again.")
        resp = _call_game_server("/register", {"username": username, "password": password})
        if resp.status_code == 409:
            print(f"  Username '{username}' is already taken. Please try again.")
            return login_or_register()
        data = resp.json()
        print(f"  Account created. Welcome, {username}!")
        return data["user_id"], data["token"]


def save_result(token: str, target_word: str, start_word: str, guesses_count: int, won: bool, time_played: int) -> None:
    '''posts a game result to the game server with the token; a failed save shouldn't crash the game'''
    try:
        requests.post(
            f"{GAME_SERVER_URL}/results",
            json={
                "target_word": target_word, "start_word": start_word,
                "guesses": guesses_count, "win": won, "time_played": time_played,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    except requests.exceptions.RequestException:
        print("  (couldn't save this result to the server)")


# ── Core helpers ──────────────────────────────────────────────────────────────
def enable_ansi_windows() -> None:
    '''initializes the console on windows, apparently'''
    if sys.platform == "win32":
        os.system("")


def clear_screen() -> None:
    '''clears terminal'''
    os.system("cls" if sys.platform == "win32" else "clear")


def score_guess(guess: str, target: str) -> list:
    '''Returns a list of 5 strings representing the color the letters in a guess should be based on the target in 2 for loops'''
    result    = ["gray"] * 5
    remaining = list(target)
    # Pass 1: exact matches
    for i in range(5):
        if guess[i] == target[i]:
            result[i]    = "green"
            remaining[i] = None
    # Pass 2: misplaced letters
    for i in range(5):
        if result[i] == "green":
            continue
        if guess[i] in remaining:
            result[i] = "yellow"
            remaining[remaining.index(guess[i])] = None
    return result


def update_letter_states(letter_states: dict, guess: str, score: list) -> None:
    '''updates the letter_states dict with the correct color status for each letter in the alphabet based on the priotity'''
    for ch, status in zip(guess, score):
        if STATUS_PRIORITY[status] > STATUS_PRIORITY[letter_states[ch]]:
            letter_states[ch] = status


# ── Rendering ─────────────────────────────────────────────────────────────────
def render_tile(letter: str, status: str) -> str:
    '''fstring formatting to return a status-colored tile for a single letter'''
    bg, fg = STATUS_COLORS[status]
    return f"{bg}{fg}{BOLD} {letter.upper()} {RESET}"


def render_board(guesses: list, scores: list) -> None:
    '''Prints the board with the list of formatted guessed words, and empty tiles past that'''
    print()
    for row in range(6):
        row_str = ""
        if row < len(scores):
            for col in range(5):
                row_str += render_tile(guesses[row][col], scores[row][col])
        else:
            for col in range(5):
                row_str += render_tile(" ", "empty")
        print("  " + row_str)
    print()


def render_keyboard(letter_states: dict) -> None:
    '''prints each row of the keyboard with colored letters from letter_states, with "unknown" as a default'''
    indents = ["  ", "    ", "       "]
    print()
    for row_str, indent in zip(KEYBOARD_ROWS, indents):
        line = indent
        for ch in row_str:
            color = KEYBOARD_FG[letter_states.get(ch, "unknown")]
            line += f"{color}{BOLD}{ch.upper()}{RESET} "
        print(line)
    print()


def print_intro() -> None:
    '''prints the title and instructions, but claude got the box wrong'''
    print()
    print("  ╔" + "═" * 21 + "╗")
    print("  ║      W O R D L      ║")
    print("  ╚" + "═" * 21 + "╝")
    print("  Guess the 5-letter word in 6 tries.")
    print("  Green=correct spot  Yellow=wrong spot  Gray=not in word")


# ── Input ─────────────────────────────────────────────────────────────────────
def get_guess(all_words: set) -> str:
    '''asks for and handles user input, returns a word if it's in the list'''
    while True:
        try:
            raw = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            sys.exit(0)
        if len(raw) != 5:
            print("  Please enter a 5-letter word.")
        elif not raw.isalpha():
            print("  Letters only — no numbers or special characters.")
        elif raw not in all_words:
            print(f"  '{raw.upper()}' is not in the word list.")
        else:
            return raw


# ── Game loop ─────────────────────────────────────────────────────────────────
def main() -> None:
    '''uses a while loop to run the game every time the user plays again, and a for loop to do each round
        gets the user's guess after printing the previous guess state (or default state), handles winning and losing outside the for loop. '''
    enable_ansi_windows()

    quiet = "--quiet" in sys.argv

    user_id, token = login_or_register()

    while True:
        target = random.choice(ANSWERS)
        guesses: list = []
        scores:  list = []
        letter_states = {chr(ord("a") + i): "unknown" for i in range(26)}
        won           = False
        start_time    = time.monotonic()

        for attempt in range(1, 7):
            if not quiet:
                clear_screen()
            print_intro()
            render_board(guesses, scores)
            render_keyboard(letter_states)
            print(f"  Attempt {attempt}/6  — type a 5-letter word and press Enter")

            guess = get_guess(ALL_WORDS)
            score = score_guess(guess, target)
            guesses.append(guess)
            scores.append(score)
            update_letter_states(letter_states, guess, score)

            if all(s == "green" for s in score):
                won = True
                break

        time_played = int(time.monotonic() - start_time)

        if not quiet:
            clear_screen()
        print_intro()
        render_board(guesses, scores)
        render_keyboard(letter_states)

        save_result(token, target, guesses[0], len(guesses), won, time_played)

        if won:
            count = len(guesses)
            print(f"  You got it in {count} guess{'es' if count != 1 else ''}! Well done!\n")
        else:
            print(f"  The word was: {BOLD}{target.upper()}{RESET}\n")
            print("  Better luck next time!\n")

        try:
            again = input("  Play again? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            again = "n"

        if again != "y":
            print("  Thanks for playing!\n")
            break


if __name__ == "__main__":
    '''int main():'''
    main()
