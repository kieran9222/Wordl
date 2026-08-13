# Wordl client
Terminal-based wordle clone:
- Six guesses for a 5-letter target word
- 14,855 guessable words and 2315 target words
- Green letters in a guess are present in their place in a target word
- Yellow letters are in the target word, but in a different place
- Gray letters aren't in the target word
- ANSI formatting
- User accounts and game history stored in PostgreSQL server
- HTTP server communication

## Requirements
Python 3. To install dependencies, run  
> pip install -r ./Client/requirements.txt

There must be a connection to a [running Wordl server](../Server/README.md) to play.
## Directions
Open the `Client/` directory. Connect to a running Wordl server by putting its URL into `.env` (see `.env.example`.)

To play, run **wordl.py** with python in a terminal:
> py wordl.py [--quiet]

On startup, choose to log in or create an account. After each game your result is saved automatically. Type valid 5-letter English words to guess, with an optional play again for multiple games. Login every 24 hours to build a daily login streak.

### Flags

Add these after the python command to change the behavior of the game:
- --quiet
    - Doesn't clear terminal before starting game

## Dashboard
To see a Server-wide leaderboard and profile page with your winrate, score and streak history, open [URL]/dashboard in your browser, [http://localhost:5000/dashboard](http://localhost:5000/dashboard) by default.