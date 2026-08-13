# Wordl
Terminal-based wordle clone:
- Six guesses for a 5-letter target word
- 14,855 guessable words and 2315 target words
- Green letters in a guess are present in their place in a target word
- Yellow letters are in the target word, but in a different place
- Gray letters aren't in the target word
- ANSI formatting
- User accounts and game history stored in PostgreSQL

## Requirements
- Python 3
- PostgreSQL server (tested with Docker)
- `psycopg[binary]` — install with:
> pip install -r requirements.txt

## Directions:
Run **wordl.py** with python in a terminal:
> py wordl.py

On startup, choose to log in or create an account. After each game your result is saved automatically. Type valid 5-letter English words to guess, with an optional play again for multiple games.

### Flags:

Add these after the python command to change the behavior of the game:
- --quiet
    - Doesn't clear terminal before starting game
- --simulate
    - Uses deterministic (alphabetical) word order between games
    - Skips login and does not write results to the database