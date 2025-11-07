import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Construct an absolute path to the database file in the project root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'playnext.db')}"

# Debug print to confirm the path is correct on startup
print(f"BACKEND IS USING DATABASE AT: {DATABASE_URL}")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    print("Initializing database tables...")
    try:
        # Use the absolute path to connect
        con = sqlite3.connect(os.path.join(PROJECT_ROOT, 'playnext.db'))
        cur = con.cursor()
        
        # Create users table with the 'is_initialized' column
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY,
          email TEXT NOT NULL UNIQUE,
          username TEXT NOT NULL UNIQUE,
          hashed_password TEXT NOT NULL,
          is_initialized BOOLEAN NOT NULL DEFAULT 0,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        # Create user_library table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_library (
          id INTEGER PRIMARY KEY,
          user_id INTEGER NOT NULL,
          game_id INTEGER NOT NULL,
          added_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
          FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
          UNIQUE (user_id, game_id)
        )""")
        
        con.commit()
        con.close()
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"An error occurred during database initialization: {e}")
