import os
from dotenv import load_dotenv

# Construct an absolute path to the .env file in the SETUP_SCRIPT directory
# This is a robust way to find the file, no matter where the app is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOTENV_PATH = os.path.join(PROJECT_ROOT, 'SETUP_SCRIPT', '.env')

# Check if the .env file exists and load it
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
    print("Successfully loaded .env file for backend.")
else:
    print("WARNING: .env file not found. Backend might not be able to connect to Twitch.")

# Load settings from environment variables
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_default_key_for_dev") # Also moving this here

# Check that the critical variables were loaded
if not CLIENT_ID or not CLIENT_SECRET:
    print("FATAL ERROR: TWITCH_CLIENT_ID or TWITCH_CLIENT_SECRET not found in environment.")
    # In a real app, you might raise an exception here