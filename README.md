# Wordl
Terminal-based wordle clone:
- Six guesses for a 5-letter target word
- 14,855 guessable words and 2315 target words
- Green letters in a guess are present in their place in a target word
- Yellow letters are in the target word, but in a different place
- Gray letters aren't in the target word
- ANSI formatting

## Directions:
Run **wordl.py** with python in a terminal:
> py wordl.py

Type valid 5-letter English words to guess, with an optional play again for multiple games
### Flags:

Add these after the python commad to change the behavior of the game:
- --quiet
    - Doesn't clear terminal before starting game
- --simulate
    - Uses deterministic (alphabetical) word order between games