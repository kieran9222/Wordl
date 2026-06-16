"""
Wordl Simulator — drives `py wordl.py --simulate --quiet` as a black-box subprocess.
No access to wordl internals or its data files; all interaction via stdin/stdout.
Word candidates come from wordfreq (independent of the game).
Requires: pip install wordfreq
"""
import csv
import os
import queue
import re
import subprocess
import sys
import threading
import time

try:
    from wordfreq import top_n_list
except ImportError:
    sys.exit("wordfreq is required: pip install wordfreq")

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPT = os.path.join(_PARENT, "wordl.py")

# Board tiles use ANSI background colors; keyboard letters use foreground only.
# Scanning for these BG codes gives board data exclusively — no keyboard overlap.
_TILE_COLORS: dict[bytes, str] = {
    b"\x1b[42m":  "green",
    b"\x1b[43m":  "yellow",
    b"\x1b[100m": "gray",
}

_PROMPT     = b"  > "
_PLAY_AGAIN = b"Play again? (y/n): "
_WIN        = b"You got it in"
_REJECTED   = b"is not in the word list"

STARTING_WORDS = ["adieu", "stare", "slate", "audio", "raise",
                  "crane", "arise", "irate", "train", "great"]

# Number of distinct answer words (one full pass of --simulate mode).
# Encoded here so the simulator can stop after a complete cycle without
# reading the game's data files.
ANSWERS_COUNT = 2314


# ── Word list ─────────────────────────────────────────────────────────────────

def build_wordlist() -> list[str]:
    """Frequency-sorted 5-letter English words from wordfreq, no game files used."""
    print("Building candidate word list from wordfreq...", file=sys.stderr)
    words = [w for w in top_n_list("en", 300_000) if len(w) == 5 and w.isalpha()]
    print(f"  {len(words)} candidates loaded", file=sys.stderr)
    return words



# ── ANSI parsing ──────────────────────────────────────────────────────────────

def parse_tiles(data: bytes) -> list[tuple[str, str]]:
    """
    Return [(letter, color), ...] for every colored board tile in raw ANSI output.
    Skips empty tiles (BG_EMPTY = \\x1b[47m) and keyboard letters (foreground only).
    """
    result = []
    i = 0
    while i < len(data):
        for seq, color in _TILE_COLORS.items():
            if data[i : i + len(seq)] == seq:
                j = i + len(seq)
                while j < len(data) and not chr(data[j]).isalpha():
                    j += 1
                if j < len(data):
                    result.append((chr(data[j]).lower(), color))
                i = j
                break
        else:
            i += 1
    return result


def parse_target_word(data: bytes) -> str | None:
    """Parse target from 'The word was: BOLD+WORD+RESET' printed on a loss."""
    m = re.search(
        rb"The word was:.*?\x1b\[1m([A-Za-z]{5})\x1b\[0m", data, re.DOTALL
    )
    return m.group(1).decode().lower() if m else None


# ── Solver ────────────────────────────────────────────────────────────────────

class Solver:
    """
    Hard-mode, no-lookahead solver.
    Maintains constraint state and returns the most frequent remaining valid word.
    """

    def __init__(self, wordlist: list[str]):
        self._all = wordlist
        self._invalid: set[str] = set()   # words rejected by the game's vocabulary check
        self._greens: dict[int, str] = {}
        self._must: set[str] = set()
        self._pos_cant: dict[int, set[str]] = {}
        self._exclude: set[str] = set()
        self._candidates: list[str] = list(wordlist)

    def reset(self):
        self._greens = {}
        self._must = set()
        self._pos_cant = {}
        self._exclude = set()
        self._candidates = [w for w in self._all if w not in self._invalid]

    def mark_invalid(self, word: str):
        """Word was not in the game's vocabulary — exclude permanently."""
        self._invalid.add(word)
        self._candidates = [w for w in self._candidates if w != word]

    def next_guess(self) -> str | None:
        """Return the highest-frequency word that satisfies all constraints."""
        for word in self._candidates:
            #greens match
            if (all(word[p] == l for p, l in self._greens.items())
                #yellows + greens
                    and self._must.issubset(set(word))
                    #yellows must move
                    and all(word[p] not in s for p, s in self._pos_cant.items())
                    #no grays
                    and not any(c in word for c in self._exclude)):
                return word
        return None

    def update(self, guess: str, score: list[str]):
        '''updates values after guess'''
        # Pass 1: greens and yellows — populate must before processing grays
        for i, (letter, status) in enumerate(zip(guess, score)):
            if status == "green":
                self._greens[i] = letter
                self._must.add(letter)
            elif status == "yellow":
                self._must.add(letter)
                self._pos_cant.setdefault(i, set()).add(letter)
        # Pass 2: grays — safe now that must is fully updated
        for letter, status in zip(guess, score):
            if status == "gray" and letter not in self._must:
                self._exclude.add(letter)
        self._candidates = [w for w in self._candidates if w != guess]


# ── Subprocess driver ─────────────────────────────────────────────────────────

class WordlDriver:
    """Drives one wordl.py process. Call play_game() repeatedly, then close()."""

    def __init__(self):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"  # force UTF-8 stdout so box-drawing chars don't crash
        # bufsize=0 gives a raw (unbuffered) stdout stream so read(N) returns
        # whatever bytes are immediately available, not blocking until N arrive.
        # Without this, BufferedReader.read(N) blocks until N bytes accumulate,
        # causing render output from one turn to bleed into the next read.
        self.proc = subprocess.Popen(
            ["py", "-u", _SCRIPT, "--simulate", "--quiet"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=_PARENT,
            env=env,
            bufsize=0,
        )
        self._q: queue.Queue[bytes] = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()
        self._read_until([_PROMPT])  # consume initial render before first game

    def _reader(self):
        while True:
            chunk = self.proc.stdout.read(256)
            if not chunk:
                break
            self._q.put(chunk)

    def _read_until(
        self, markers: list[bytes], timeout: float = 20.0
    ) -> tuple[bytes, bytes | None]:
        data = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                data += self._q.get(timeout=0.05)
            except queue.Empty:
                if self.proc.poll() is not None:
                    break
                continue
            for m in markers:
                if m in data:
                    return data, m
        return data, None

    def _send(self, text: str):
        self.proc.stdin.write((text + "\n").encode())
        self.proc.stdin.flush()

    def play_game(
        self, starting_word: str, solver: Solver
    ) -> tuple[int, str | None]:
        """
        Play one game.
        Returns (guesses_used, target_word).
        guesses_used == 7 means the game was lost (or solver failed).
        target_word is the winning guess on a win, or parsed from game output on a loss.
        """
        solver.reset()
        attempt = 0
        last_accepted: str | None = None

        while attempt < 6:
            guess = starting_word if attempt == 0 else solver.next_guess()

            if guess is None:
                # Solver exhausted valid candidates — drain the game with any known word
                for w in solver._all:
                    if w not in solver._invalid:
                        guess = w
                        break
                if guess is None:
                    return 7, None

            self._send(guess)
            data, marker = self._read_until([_PROMPT, _PLAY_AGAIN])

            if _REJECTED in data:
                solver.mark_invalid(guess)
                continue  # attempt not counted; game still at same prompt

            attempt += 1
            last_accepted = guess
            tiles = parse_tiles(data)
            score = [c for _, c in tiles[-5:]] if len(tiles) >= 5 else []

            if marker == _PLAY_AGAIN:
                if _WIN in data:
                    return attempt, last_accepted  # winning guess == target
                return 7, parse_target_word(data)

            if score:
                solver.update(guess, score)

        return 7, None  # safety fallback (normal play returns inside the loop)

    def start_next_game(self):
        self._send("y")
        self._read_until([_PROMPT])

    def close(self):
        try:
            self._send("n")
        except OSError:
            pass
        self.proc.terminate()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    wordlist = build_wordlist()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.csv")
    total = len(STARTING_WORDS) * ANSWERS_COUNT
    done = 0

    with open(out, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["starting_word", "target_word", "guesses"])

        for sw in STARTING_WORDS:
            print(f"Starting word: {sw}", file=sys.stderr)
            driver = WordlDriver()
            solver = Solver(wordlist)

            for game_idx in range(ANSWERS_COUNT):
                guesses, target = driver.play_game(sw, solver)
                writer.writerow([sw, target or f"unknown_{game_idx + 1}", guesses])
                done += 1

                if game_idx < ANSWERS_COUNT - 1:
                    driver.start_next_game()

                if done % 500 == 0:
                    print(f"  {done}/{total}", file=sys.stderr)

            driver.close()

    print(f"Done. Results written to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
