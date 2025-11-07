# SETUP_SCRIPT/verify_db.py

import sqlite3
import os

# Go up one directory from SETUP_SCRIPT to find the root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "playnext.db")

if not os.path.exists(DB_PATH):
    print(f"Error: Database file not found at '{DB_PATH}'")
    print("Please run the seed_db.py script first.")
    exit()

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

try:
    count = cur.execute("SELECT count(*) FROM games").fetchone()[0]
    print(f"✅ Database verification successful.")
    print(f"Total rows in 'games' table: {count}")

    print("\nTop 10 games by popularity:")
    # Updated query to select 'popularity' and 'total_rating_count'
    for name, popularity, rc in cur.execute(
        "SELECT name, popularity, total_rating_count FROM games ORDER BY popularity DESC LIMIT 10"
    ):
        print(f"- {name} (Popularity: {popularity}, Ratings: {rc})")

except sqlite3.OperationalError as e:
    print(f"An error occurred while querying the database: {e}")

finally:
    con.close()