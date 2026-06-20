# Simulator
A python-based wordl game simulator to test the 10 most common starting words in Wordle against all 2315 target words.
- Runs 23150 games of **wordl.py** in ~3 minutes
- Plays wordle in NYT games hard mode, using every hint given in the next guess
- Uses word frequency data to guess the next word
- Writes results to **data/results.csv** formatted as: 

    starting_word, target_word, guesses

### Instructions
Run **simulator.py** with python in a terminal:
> py simulator/simulate.py 

# Visualizer
Produces two images with Matplotlib that visualize data from the simulator in **results.csv**:
- A histogram showing the number of guesses required for each of the 10 starting words, their average guesses required and win rate
- An image listing the words that were always guesses in 2, and words that always failed to be guessed

Both images are saved as PNGs to **simulator/**

### Instructions
1. Run **Simulate.py** to create **results.csv**
1. Run **visualize.py** with Python in a terminal:
    > py simulator/visualize.py
