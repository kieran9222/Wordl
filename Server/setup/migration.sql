CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    win_streak INT NOT NULL CHECK (win_streak >= 0) DEFAULT 0,
    longest_streak INT NOT NULL CHECK (longest_streak >= 0) DEFAULT 0,
    total_wins INT NOT NULL CHECK (total_wins >= 0) DEFAULT 0,
    total_games INT NOT NULL CHECK (total_games >= 0) DEFAULT 0,
    daily_login_streak INT NOT NULL CHECK (daily_login_streak >= 0) DEFAULT 0,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_word VARCHAR(50) NOT NULL,
    start_word VARCHAR(50) NOT NULL,
    guesses INT NOT NULL CHECK (guesses >= 0),
    win BOOLEAN NOT NULL,
    timer INT NOT NULL CHECK (timer >= 0)
);

CREATE INDEX IF NOT EXISTS idx_results_user_id ON results(user_id);
