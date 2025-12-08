import os
from recommender import train_and_save_model

# Construct the absolute path to the database file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'playnext.db')

if __name__ == '__main__':
    print("--- Starting Recommender Model Training ---")
    if not os.path.exists(DB_PATH):
        print(f"FATAL: Database not found at '{DB_PATH}'.")
        print("Please run the SETUP_SCRIPT/seed_db.py first.")
    else:
        train_and_save_model(DB_PATH)
        print("--- Recommender Model Training Complete ---")
        print("You can now start the FastAPI server.")