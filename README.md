## 🗄️ Database Setup (`SETUP_SCRIPT/`)

This directory contains all the necessary scripts to perform a one-time setup of the local project database. The main script, `seed_db.py`, connects to the IGDB API, fetches data for the top ~20,000 most popular games, and stores them in a local SQLite database named `playnext.db` in the project root.

### File Breakdown

- **`seed_db.py`**:
  The primary script for building the database. It authenticates with the Twitch API, fetches game data in batches of 500, processes the data, and saves it to the `playnext.db` file. It is idempotent, meaning you can run it multiple times to update the database without errors.

- **`verify_db.py`**:
  A utility script to check if the database was created successfully. It prints the total number of games in the table and lists the top 10 games by their calculated popularity score.

- **`smoke_test.py`**:
  A minimal script to perform a quick "smoke test" on your API credentials. It authenticates and attempts to fetch 5 games to confirm that your `.env` configuration is correct and that the IGDB API is reachable.

- **`requirements.txt`**:
  Contains the necessary Python packages (`requests`, `python-dotenv`) required by the setup scripts.

- **`.env.example` / `.env`**:
  Used for managing API credentials securely. You must create your own `.env` file with your Twitch App credentials.

### How to Set Up the Database

Follow these steps to create and populate your local `playnext.db` file.

**1. Install Dependencies**

First, it is highly recommended to create and activate a Python virtual environment. Then, install the required packages.

```bash
# Navigate to the project root
cd /path/to/PlayNext-Video-Game-Recommender-System

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r SETUP_SCRIPT/requirements.txt
```

**2. Create a `.env` Configuration File**

In the `SETUP_SCRIPT/` directory, create a file named `.env`.

Now, open `SETUP_SCRIPT/.env` and replace the placeholders with your actual **Twitch Application Client ID and Client Secret**.

```dotenv
# SETUP_SCRIPT/.env

TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here
```

**3. Run the Seeding Script**

With your dependencies installed and credentials configured, run the main seeding script from the project root directory.

```bash
python SETUP_SCRIPT/seed_db.py
```

The script will show its progress as it authenticates, fetches each page of data, and saves it to the database. This process may take several minutes to complete as it fetches 40 pages of data with pauses in between.

**4. Verify the Database**

After the script finishes, a `playnext.db` file will be present in your project's root directory. You can run the verification script to confirm its contents:

```bash
python SETUP_SCRIPT/verify_db.py
```

If successful, it will print the total number of games (which should be close to 20,000) and list the top 10 most popular games found. Your database is now ready for the main application.

