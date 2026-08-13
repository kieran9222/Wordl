# Simulator
Fills database with `num_players` (default 100) players with realistic names from **Faker**, each playing between `game_min` and `game_max` games (default 12, 100). One third of players will try and play strategically to gain information, the rest will guess the next-best word that satisfies the guesses. Inserts fake playtimes.
### Instructions
run **simulator.py** with python in a terminal, optionally passing in 3 parameters:
> py simulator/simulate.py [num_players] [game_min] [game_max]

