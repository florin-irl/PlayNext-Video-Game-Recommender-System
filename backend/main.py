# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from fastapi.middleware.cors import CORSMiddleware

from . import models, schemas, security
# --- MODIFICATION: get_db is now imported from database.py ---
from .database import SessionLocal, init_db, get_db

init_db()
app = FastAPI()

origins = ["http://127.0.0.1:5500", "http://localhost:5500"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- The get_db function is now REMOVED from this file ---

# The rest of the file remains the same, as it already uses Depends(get_db)
@app.post("/register", response_model=schemas.UserInDB)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # ... (code is unchanged)
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user_by_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=schemas.LoginResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # ... (code is unchanged)
    user = security.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "user": user}

@app.get("/users/me", response_model=schemas.UserInDB)
async def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user

@app.get("/games/onboarding", response_model=List[schemas.Game])
def get_onboarding_games(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    games = db.query(models.Game).order_by(models.Game.popularity.desc()).limit(30).all()
    return games

@app.post("/users/me/library/initialize", status_code=status.HTTP_204_NO_CONTENT)
def initialize_user_library(
    library_data: schemas.InitialLibraryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # ... (code is unchanged)
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
    db.add(current_user)
    db.commit()
    return

@app.get("/users/me/library/last-added", response_model=List[schemas.Game])
def get_last_added_games(
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Fetches the last N games added to the current user's library.
    """
    # 1. Get the last 'limit' entries from user_library, sorted by when they were added
    last_added_entries = (
        db.query(models.UserLibrary)
        .filter(models.UserLibrary.user_id == current_user.id)
        .order_by(models.UserLibrary.added_at.desc())
        .limit(limit)
        .all()
    )

    if not last_added_entries:
        return []

    # 2. Extract just the game IDs from those entries
    last_added_game_ids = [entry.game_id for entry in last_added_entries]

    # 3. Fetch the full game details for those IDs from the 'games' table
    games = db.query(models.Game).filter(models.Game.id.in_(last_added_game_ids)).all()
    
    # 4. We need to preserve the 'added_at' order, which the 'in_' query doesn't
    #    So, we re-sort the results based on the original ordered list of IDs.
    game_map = {game.id: game for game in games}
    sorted_games = [game_map[game_id] for game_id in last_added_game_ids if game_id in game_map]

    return sorted_games

@app.get("/users/me/library", response_model=List[schemas.Game])
def get_user_library(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Fetches all games in the current user's library, sorted alphabetically.
    """
    # 1. Get all of the user's library entries
    library_entries = (
        db.query(models.UserLibrary)
        .filter(models.UserLibrary.user_id == current_user.id)
        .all()
    )

    if not library_entries:
        return []

    # 2. Extract the game IDs
    game_ids = [entry.game_id for entry in library_entries]

    # 3. Fetch the full game details for those IDs, sorted by name
    games = (
        db.query(models.Game)
        .filter(models.Game.id.in_(game_ids))
        .order_by(models.Game.name.asc())
        .all()
    )
    
    return games

@app.get("/games/search", response_model=List[schemas.Game])
def search_games(
    q: str, # The search query parameter
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """ Searches for games in the database by name. """
    if not q or len(q) < 3:
        # Don't search for very short strings to avoid too many results
        return []
    
    search_term = f"%{q}%"
    found_games = (
        db.query(models.Game)
        .filter(models.Game.name.ilike(search_term)) # ilike is case-insensitive
        .limit(10) # Return a max of 10 results
        .all()
    )
    return found_games


@app.post("/users/me/library", response_model=schemas.Game)
def add_game_to_library(
    request: schemas.AddGameRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """ Adds a single game to the current user's library. """
    # 1. Check if the game exists in the main games table
    game_to_add = db.query(models.Game).filter(models.Game.id == request.game_id).first()
    if not game_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    # 2. Check if the user already has this game in their library
    existing_entry = (
        db.query(models.UserLibrary)
        .filter(
            models.UserLibrary.user_id == current_user.id,
            models.UserLibrary.game_id == request.game_id
        )
        .first()
    )
    if existing_entry:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Game already in library")

    # 3. Add the game to the library
    new_library_entry = models.UserLibrary(user_id=current_user.id, game_id=request.game_id)
    db.add(new_library_entry)
    db.commit()

    return game_to_add
