# SETUP_SCRIPT/seed_db.py

import os
import time
import json
import sqlite3
import requests
from dotenv import load_dotenv

# --- 1. CONFIGURATION & SETUP ---

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "playnext.db")

ENV_PATHS = [os.path.join(os.path.dirname(__file__), ".env"), os.path.join(ROOT, ".env")]
for p in ENV_PATHS:
    if os.path.exists(p):
        load_dotenv(p)
        break

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "").strip()

PAGE_SIZE = 500
PAGES_TO_FETCH = 40
REQUEST_PAUSE = 0.25

if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit("ERROR: Missing TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET in .env file.")


# --- 2. API INTERACTION FUNCTIONS ---

def get_twitch_token():
    print("→ Authenticating with Twitch to get API token...")
    try:
        r = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
            timeout=30
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        print("✅ Token acquired successfully.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Could not get Twitch token. Error: {e}")
        raise SystemExit()

def fetch_igdb_games_page(token, offset):
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}

    # MODIFICATION: Removed 'follows' from fields and sort clauses.
    query_clauses = [
        "fields id,name,summary,cover.image_id,total_rating_count,genres,keywords,platforms",
        "where (cover != null & total_rating_count > 0)",
        "sort total_rating_count desc", # Sorting only by rating count now
        f"limit {PAGE_SIZE}",
        f"offset {offset}"
    ]
    query = ";".join(query_clauses) + ";"

    try:
        r = requests.post("https://api.igdb.com/v4/games", data=query.encode('utf-8'), headers=headers, timeout=60)

        if r.status_code >= 400:
            print(f"\n--- IGDB API ERROR ---")
            print(f"Status: {r.status_code}")
            print(f"Query Sent: {query}")
            print(f"Response Body: {r.text}")
        
        r.raise_for_status()
        return r.json()

    except requests.exceptions.RequestException as e:
        print(f"ERROR: API request failed for offset {offset}. Error: {e}")
        return []


# --- 3. DATABASE FUNCTIONS ---

def init_db():
    print("→ Initializing database...")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # MODIFICATION: Removed 'follows' column from the table schema.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS games(
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      summary TEXT,
      cover_url TEXT,
      popularity REAL,
      total_rating_count INTEGER,
      genres_json TEXT,
      keywords_json TEXT,
      platforms_json TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_games_name ON games(name)")
    con.commit()
    con.close()
    print("✅ Database initialized.")

def upsert_games_batch(rows):
    if not rows:
        return 0
        
    con = sqlite3.connect(DB_PATH)
    
    # MODIFICATION: Removed 'follows' from the INSERT and UPDATE statements.
    sql = """INSERT INTO games
      (id,name,summary,cover_url,popularity,total_rating_count,
       genres_json,keywords_json,platforms_json,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
      ON CONFLICT(id) DO UPDATE SET
        name=excluded.name,
        summary=excluded.summary,
        cover_url=excluded.cover_url,
        popularity=excluded.popularity,
        total_rating_count=excluded.total_rating_count,
        genres_json=excluded.genres_json,
        keywords_json=excluded.keywords_json,
        platforms_json=excluded.platforms_json,
        updated_at=datetime('now')
    """
    
    data_to_insert = []
    for game in rows:
        cover = game.get("cover")
        cover_url = f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover['image_id']}.jpg" if cover else None
        
        rating_cnt = game.get("total_rating_count", 0) or 0
        
        # MODIFICATION: Popularity is now solely based on rating count.
        popularity = float(rating_cnt)

        # MODIFICATION: Removed 'follows' from the data tuple.
        data_to_insert.append((
            game["id"], game["name"], game.get("summary"), cover_url,
            popularity, rating_cnt,
            json.dumps(game.get("genres", []) or []),
            json.dumps(game.get("keywords", []) or []),
            json.dumps(game.get("platforms", []) or [])
        ))
        
    con.executemany(sql, data_to_insert)
    con.commit()
    con.close()
    return len(data_to_insert)

# --- 4. MAIN EXECUTION ---

def main():
    print("🚀 Starting PlayNext Database Seeding Script")
    init_db()
    token = get_twitch_token()
    
    total_games_processed = 0
    print(f"\n🔥 Starting to fetch {PAGES_TO_FETCH * PAGE_SIZE} games from IGDB...")

    for i in range(PAGES_TO_FETCH):
        offset = i * PAGE_SIZE
        print(f"• Fetching Page {i+1}/{PAGES_TO_FETCH} (offset={offset})...")
        
        rows = fetch_igdb_games_page(token, offset)
        
        if not rows:
            print("• No more games returned from API. Stopping.")
            break
            
        inserted_count = upsert_games_batch(rows)
        total_games_processed += inserted_count
        
        print(f"  └─> Saved {inserted_count} games to the database.")
        time.sleep(REQUEST_PAUSE)

    print(f"\n✅ Done. Processed a total of {total_games_processed} games.")
    print(f"Database is ready at: {DB_PATH}")

if __name__ == "__main__":
    main()