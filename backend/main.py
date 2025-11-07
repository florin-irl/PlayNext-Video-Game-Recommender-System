from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

from . import models, schemas, security
from .database import SessionLocal, init_db

init_db()
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserInDB)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
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
    if current_user.is_initialized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already initialized.")
    
    if len(library_data.game_ids) != 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please select exactly 5 games.")

    # TODO: Create user_library entries in the database for each game_id.
    print(f"User {current_user.username} selected game IDs: {library_data.game_ids}")
    
    current_user.is_initialized = True
    db.add(current_user)
    db.commit()
    
    return