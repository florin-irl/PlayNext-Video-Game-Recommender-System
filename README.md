# PlayNext — Video Game Recommender System

PlayNext is a lightweight recommender system for video games. It provides a FastAPI backend that serves user authentication, user libraries, game discovery and a content-based recommender built from a scraped games dataset. A small static frontend is included for demos and manual testing.

**Made by**
Florin-Andrei Ivana

---

## Screenshots

**Onboarding Process that solves the cold start problem**
<img width="1918" height="870" alt="image" src="https://github.com/user-attachments/assets/ea96d604-cf8b-4d48-989d-f0f407e0bb37" />

**Home Screen - Shows last added games to library, button for adding last recently played game, and menu bar for the different sections**
<img width="1918" height="856" alt="image" src="https://github.com/user-attachments/assets/c28e8fe4-9c36-4cab-92c9-6da47dddf9d1" />

**My Games - Can manage user library**
<img width="1918" height="865" alt="image" src="https://github.com/user-attachments/assets/77c9d221-d514-4e24-b7d9-534c3d1b58b8" />
<img width="1918" height="865" alt="image" src="https://github.com/user-attachments/assets/95663fda-aed9-4359-a56d-a6ca02185099" />

**Recommendations - Show the content based recommendation system, allows users to add games to library by selecting them**
<img width="1918" height="862" alt="image" src="https://github.com/user-attachments/assets/5cd7adaf-ebf3-4b89-9f6d-97dbf765a179" />
<img width="1917" height="855" alt="image" src="https://github.com/user-attachments/assets/a390d593-af6d-4de7-b6b8-47a048b494e0" />

**Popular Now - Takes advantage of the already used Twitch API to display actively popular games that are most watched on twitch.tv**
<img width="1918" height="865" alt="image" src="https://github.com/user-attachments/assets/63d23858-7f6d-4a10-aaf9-068aa3886c90" />


---

**Contents (top-level)**
- `backend/` — FastAPI application, database models, recommender training and API entrypoint.
- `frontend/` — Static frontend (HTML/JS/CSS) used to demo the app locally.
- `SETUP_SCRIPT/` — Scripts to seed the local SQLite database from the Twitch/IGDB data and helpers to verify it.
- `playnext.db` — (generated) SQLite database created by the seeding script.

---

## Quickstart (development)

1. Create and activate a Python virtual environment in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
pip install -r backend/requirements.txt
pip install -r SETUP_SCRIPT/requirements.txt
```

3. Create `.env` for Twitch credentials and secret key:

- Copy `SETUP_SCRIPT/.env.example` (or create `SETUP_SCRIPT/.env`) and populate:

```
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=a_secure_secret_for_jwt_or_sessions
```

The backend reads environment variables from `SETUP_SCRIPT/.env` (see `backend/config.py`).

4. Seed the database (one-time):

```powershell
# From project root
python SETUP_SCRIPT/seed_db.py
```

This will create `playnext.db` in the project root containing the games dataset used for recommendations.

5. Train the recommender (generates model files used by the API):

```powershell
python backend/train_recommender.py
```

This creates three files under `backend/`: `similarity_matrix.pkl`, `game_indices.pkl`, and `game_list.pkl`.

6. Run the backend API (development mode):

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for interactive API documentation (Swagger UI).

7. Serve the frontend locally (static files):

You can open files directly with a static server. Example using Python's built-in server from the `frontend/` folder:

```powershell
cd frontend
python -m http.server 5500
# open http://127.0.0.1:5500/home.html
```

The backend allows CORS from `http://127.0.0.1:5500` and `http://localhost:5500`, which matches this setup.

---

## Architecture & Key Components

- Backend: FastAPI application at `backend/main.py`. It exposes endpoints for registration/login, user libraries, search, popular games and recommendations. Authentication is JWT-based (see `backend/security.py`).
- Database: SQLite file `playnext.db` in the project root. Models and DB helpers are in `backend/database.py` and `backend/models.py`.
- Recommender: Content-based recommender implemented in `backend/recommender.py`. The training script `backend/train_recommender.py` reads `playnext.db`, vectorizes combined text fields (summary, genres, keywords) and computes cosine similarity. Trained artifacts are saved as pickles in `backend/` and loaded by `backend/main.py` on startup.
- Frontend: Minimal static UI in `frontend/` for manual testing and demos (no Node.js build required).

---

## Environment variables

Place the following in `SETUP_SCRIPT/.env`:

- `TWITCH_CLIENT_ID` — Twitch application client ID (used by seeding and some discovery endpoints).
- `TWITCH_CLIENT_SECRET` — Twitch application client secret.
- `SECRET_KEY` — Secret key used by backend for JWT signing (optional; a default is provided for development).

Important: keep these values private; do not commit them to version control.

---

## API Summary (selected endpoints)

All API endpoints are prefixed at the root of the FastAPI server (default `http://127.0.0.1:8000`). Use the interactive docs at `/docs` for request/response shapes.

- `POST /register` — register a new user. Accepts `UserCreate` payload and returns created user.
- `POST /login` — form-data `username`/`password` to retrieve an access token.
- `GET /users/me` — returns the current authenticated user (requires Bearer token).
- `GET /users/me/library` — list games in the authenticated user's library.
- `POST /users/me/library` — add a game to the user's library (body: `{ "game_id": <id> }`).
- `POST /users/me/library/initialize` — initialize onboarding library with 5 game IDs.
- `GET /games/onboarding` — returns a set of onboarding candidates (popular by internal metric).
- `GET /games/search?q=<term>` — search games by name (min 3 chars recommended).
- `GET /games/popular` — fetches top Twitch games (requires Twitch credentials via `.env`).
- `GET /recommendations/{game_id}` — returns content-based recommendations for the provided game ID. The recommender pickles must exist (run `python backend/train_recommender.py`).

Refer to `backend/schemas.py` for models and types used by the API.

---

## Development notes & troubleshooting

- If `backend/main.py` prints "WARNING: Recommender model files not found", run `python backend/train_recommender.py` to generate the pickles.
- If the Twitch authentication fails, double-check `SETUP_SCRIPT/.env` and run `SETUP_SCRIPT/smoke_test.py`.
- Database file `playnext.db` should be present in the project root after seeding. If missing, re-run `python SETUP_SCRIPT/seed_db.py`.

---

## Tests & Setup helpers

- `SETUP_SCRIPT/seed_db.py` — produces `playnext.db` by calling the Twitch/IGDB APIs.
- `SETUP_SCRIPT/verify_db.py` — lightweight checks to verify database contents.
- `SETUP_SCRIPT/smoke_test.py` — verifies Twitch credentials and ability to fetch sample game data.

---

## Contributing

If you plan to modify the project:

- Work on feature branches and open PRs for review.
- Keep secrets out of source control (use `SETUP_SCRIPT/.env` locally).

---

## Contact

For questions about the code or dataset, contact me on:
[LinkedIn](https://www.linkedin.com/in/florin-andrei-ivana-307776239/)
[GitHub](https://github.com/florin-irl)
---
