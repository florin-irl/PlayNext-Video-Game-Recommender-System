import requests
import pickle
import os
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Import from our local modules
from . import models, schemas, security, config
from .database import init_db, get_db

# Initialize database tables on startup
init_db()

app = FastAPI()

# Construct absolute paths to the model files
BACKEND_ROOT = os.path.dirname(__file__) # This gets the 'backend/' directory path
SIMILARITY_MATRIX_PATH = os.path.join(BACKEND_ROOT, 'similarity_matrix.pkl')
GAME_INDICES_PATH = os.path.join(BACKEND_ROOT, 'game_indices.pkl')
GAME_LIST_PATH = os.path.join(BACKEND_ROOT, 'game_list.pkl')


# Load the files into global variables
try:
    with open(SIMILARITY_MATRIX_PATH, 'rb') as f:
        similarity_matrix = pickle.load(f)
    with open(GAME_INDICES_PATH, 'rb') as f:
        game_indices = pickle.load(f)
    with open(GAME_LIST_PATH, 'rb') as f:
        game_list = pickle.load(f)

    index_to_game_id = {v: k for k, v in game_indices.items()}

    print("Recommender models loaded successfully.")
except FileNotFoundError:
    print("WARNING: Recommender model files not found. Run 'python backend/train_recommender.py' to generate them.")
    similarity_matrix = None
    game_indices = None
    game_list = None
    index_to_game_id = None

# Define allowed origins for CORS
origins = ["http://127.0.0.1:5500", "http://localhost:5500"]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- User Authentication Endpoints ---

@app.post("/register", response_model=schemas.UserInDB)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    db_user_by_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.LoginResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = security.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "user": user}

@app.get("/users/me", response_model=schemas.UserInDB)
async def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user


# --- Library & Onboarding Endpoints ---

@app.get("/users/me/library", response_model=List[schemas.Game])
def get_user_library(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    library_entries = db.query(models.UserLibrary).filter(models.UserLibrary.user_id == current_user.id).all()
    if not library_entries:
        return []
    game_ids = [entry.game_id for entry in library_entries]
    games = db.query(models.Game).filter(models.Game.id.in_(game_ids)).order_by(models.Game.name.asc()).all()
    return games

@app.post("/users/me/library", response_model=schemas.Game)
def add_game_to_library(request: schemas.AddGameRequest, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    game_to_add = db.query(models.Game).filter(models.Game.id == request.game_id).first()
    if not game_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    existing_entry = db.query(models.UserLibrary).filter(models.UserLibrary.user_id == current_user.id, models.UserLibrary.game_id == request.game_id).first()
    if existing_entry:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game already in library")
    new_library_entry = models.UserLibrary(user_id=current_user.id, game_id=request.game_id)
    db.add(new_library_entry)
    db.commit()
    return game_to_add

@app.get("/users/me/library/last-added", response_model=List[schemas.Game])
def get_last_added_games(limit: int = 3, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    last_added_entries = db.query(models.UserLibrary).filter(models.UserLibrary.user_id == current_user.id).order_by(models.UserLibrary.added_at.desc()).limit(limit).all()
    if not last_added_entries:
        return []
    last_added_game_ids = [entry.game_id for entry in last_added_entries]
    games = db.query(models.Game).filter(models.Game.id.in_(last_added_game_ids)).all()
    game_map = {game.id: game for game in games}
    sorted_games = [game_map[game_id] for game_id in last_added_game_ids if game_id in game_map]
    return sorted_games

@app.post("/users/me/library/initialize", status_code=status.HTTP_204_NO_CONTENT)
def initialize_user_library(library_data: schemas.InitialLibraryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.is_initialized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already initialized.")
    if len(library_data.game_ids) != 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select exactly 5 games.")
    for game_id in library_data.game_ids:
        game_exists = db.query(models.Game).filter(models.Game.id == game_id).first()
        if game_exists:
            library_entry = models.UserLibrary(user_id=current_user.id, game_id=game_id)
            db.add(library_entry)
    current_user.is_initialized = True
    # The redundant `db.add(current_user)` is removed here to fix the bug
    db.commit()
    return


# --- Game Discovery Endpoints ---

@app.get("/games/onboarding", response_model=List[schemas.Game])
def get_onboarding_games(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    games = db.query(models.Game).order_by(models.Game.popularity.desc()).limit(30).all()
    return games

@app.get("/games/search", response_model=List[schemas.Game])
def search_games(q: str, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    if not q or len(q) < 3:
        return []
    search_term = f"%{q}%"
    found_games = db.query(models.Game).filter(models.Game.name.ilike(search_term)).limit(10).all()
    return found_games



def get_twitch_app_access_token():
    try:
        response = requests.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": config.CLIENT_ID,
                "client_secret": config.CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting Twitch token: {e}")
        return None

@app.get("/games/popular", response_model=List[schemas.PopularGame])
def get_popular_games(limit: int = 10, current_user: models.User = Depends(security.get_current_user)):
    token = get_twitch_app_access_token()
    if not token:
        raise HTTPException(status_code=500, detail="Could not authenticate with Twitch")
    headers = {"Client-ID": config.CLIENT_ID, "Authorization": f"Bearer {token}"}
    twitch_response = requests.get(f"https://api.twitch.tv/helix/games/top?first={limit}", headers=headers)
    twitch_response.raise_for_status()
    top_games_data = twitch_response.json()["data"]
    popular_games = []
    for game in top_games_data:
        cover_url = game.get("box_art_url", "").replace("{width}", "285").replace("{height}", "380")
        viewers = game.get("viewer_count", 0)
        viewer_count_str = f"{round(viewers / 1000)}K viewers" if viewers >= 1000 else f"{viewers} viewers"
        popular_games.append({"name": game["name"], "cover_url": cover_url, "viewer_count": viewer_count_str})
    return popular_games


@app.get("/recommendations/{game_id}", response_model=List[schemas.Game])
def get_recommendations(
        game_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(security.get_current_user)
):
    """
    Returns content-based recommendations for a given game ID.
    """
    # Check if the models were loaded correctly
    if similarity_matrix is None or game_indices is None:
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail="Recommender model is not available."
        )

    # Check if the requested game_id is in our model
    if game_id not in game_indices:
        raise HTTPException(
            status_code=404,
            detail="Game not found in the recommender model."
        )

    # 1. Get the index of the game that matches the ID
    idx = game_indices[game_id]

    # 2. Get the pairwise similarity scores of all games with that game
    sim_scores = list(enumerate(similarity_matrix[idx]))

    # 3. Sort the games based on the similarity scores in descending order
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # 4. Get the scores of the 10 most similar games (index 0 is the game itself)
    sim_scores = sim_scores[1:11]

    # 5. Get the game indices from the sorted scores
    recommended_game_indices = [i[0] for i in sim_scores]

    # 6. Get the game IDs from the indices
    recommended_game_ids = [index_to_game_id[i] for i in recommended_game_indices]

    # 7. Fetch the full game details from the main database
    recommended_games = db.query(models.Game).filter(models.Game.id.in_(recommended_game_ids)).all()

    # 8. Re-sort the final list to match the recommendation order
    game_map = {game.id: game for game in recommended_games}
    sorted_recommendations = [game_map[gid] for gid in recommended_game_ids if gid in game_map]

    return sorted_recommendations

@app.get("/games/{game_id}", response_model=schemas.Game)
def get_game_details(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """ Fetches the details for a single game by its ID. """
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
