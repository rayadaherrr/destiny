"""
The database: users and the trips they have logged.
SQLite is a database that lives in one file (destiny.db). No server needed.
"""
import hashlib
import hmac
import os
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "destiny.db"


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row   # rows behave like dicts: row["username"]
    return conn


def init_db():
    """Create the tables if they do not exist yet. Safe to run every time."""
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                bio           TEXT NOT NULL DEFAULT '',
                home_city     TEXT NOT NULL DEFAULT 'lisbon'
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                city_id    TEXT NOT NULL,
                start_date TEXT,
                end_date   TEXT,
                rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                review     TEXT NOT NULL DEFAULT '',
                budget_eur REAL
            )""")


# ------------------------------------------------------------ passwords
def hash_password(password, salt=None):
    """Never store a password as text. Store a salted hash instead."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + digest.hex()


def check_password(password, stored):
    salt_hex, _ = stored.split(":")
    candidate = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(candidate, stored)


# ------------------------------------------------------------ users
def create_user(username, password):
    """Returns (user_id, None) on success, or (None, 'error message')."""
    username = username.strip().lower()
    if len(username) < 3:
        return None, "Username must have at least 3 characters."
    if len(password) < 6:
        return None, "Password must have at least 6 characters."
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password)),
            )
            return cur.lastrowid, None
    except sqlite3.IntegrityError:
        return None, "That username is already taken."


def login(username, password):
    """Returns the user's id, or None if the username or password is wrong."""
    with connect() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
    if row and check_password(password, row["password_hash"]):
        return row["id"]
    return None


def get_user(user_id):
    with connect() as conn:
        return conn.execute(
            "SELECT id, username, bio, home_city FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def list_users():
    with connect() as conn:
        return conn.execute("SELECT id, username FROM users ORDER BY username").fetchall()


def update_bio(user_id, bio):
    with connect() as conn:
        conn.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, user_id))


# ------------------------------------------------------------ trips
def add_trip(user_id, city_id, rating, review="", start_date=None, end_date=None, budget_eur=None):
    with connect() as conn:
        conn.execute(
            "INSERT INTO trips (user_id, city_id, start_date, end_date, rating, review, budget_eur) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, city_id, start_date, end_date, rating, review, budget_eur),
        )


def user_trips(user_id):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM trips WHERE user_id = ? ORDER BY COALESCE(start_date, '') DESC, id DESC",
            (user_id,),
        ).fetchall()


def delete_trip(user_id, trip_id):
    """The user_id in the WHERE means you can only delete your own trips."""
    with connect() as conn:
        conn.execute("DELETE FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id))


def user_stats(user_id):
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n, COUNT(DISTINCT city_id) AS cities, AVG(rating) AS avg_rating "
            "FROM trips WHERE user_id = ?", (user_id,),
        ).fetchone()
    return {"trips": row["n"], "cities": row["cities"], "avg_rating": row["avg_rating"]}