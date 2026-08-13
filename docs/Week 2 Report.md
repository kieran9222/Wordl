# Week 2 Report

## Updates

- Cleaned up and divided repository as directed, added READMEs, changes file paths in the python files
- Pushed directly to main and merged that with db-integration so that they both start clean
- Learned why databases are better than hard-coded file paths
- Made sure claude could see the database (it ran docker ps or something)
- Wrote prompt for user integration
- I never told it to use hashes, but it's probably good it did anyway
- I asked for a login/new user prompt, which it didn't do, so it will have to fix this becuase no one wants to create a new user when they mistype their username
- Claude wanted to do ALTER TABLE for me with DOCKER EXEC, but I tried it in beekeeper for fun.
- After minimal testing, everything seems to work and update on beekeeper studio.
- I had claude update README.MedicinaeDoctor because I was very lazy
- I will like to learn more about what kind of server docker/postgres is operating, but for now that remains nebulous because I'm leaving

## Wordle User Integration

The goal here is simple: update the `wordl.py` game to have a user system, automatically fill out table for every game played. With this done, I can move on to adjusting the simulator and making the database more advanced

**"Update wordl.py to use the postgres server with psycopg. Create login/new user prompt when starting Wordl, create a new entry in users if a new user is created. After every game completes, add the game data to a new entry in results. Fill in every field."**

I will run this in plan mode so it doesn't run on a misunderstanding again (it still misunderstood).

**"Change the implementation have a prompt asking if a user wants to make an accouint or login before prompting them for a username, confirm password when making an account"**

last_login should also default to the creation date, since if the user plays a game after creating their account, it won't add a timestamp. Even if they exit the game immediately after creating an account, it should still count as a login.

**"update reademe.md in the main directory to reflect the recent changes in the feature list/instructions, following the existing structure"**

***TODO***: a time_played column for `results`\
***TODO***: add docstrings to the new and improved `wordl.py`


### User database prototype
- Wordl game asks users to create an account or login
- Account stored in `users`, password is hashed
- Games played are recorded in `results`, linked to user