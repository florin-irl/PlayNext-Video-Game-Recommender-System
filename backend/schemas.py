from pydantic import BaseModel, EmailStr
from typing import List

class Game(BaseModel):
    id: int
    name: str
    cover_url: str | None = None
    
    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserInDB(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_initialized: bool
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInDB

class TokenData(BaseModel):
    username: str | None = None

class InitialLibraryCreate(BaseModel):
    game_ids: List[int]

class AddGameRequest(BaseModel):
    game_id: int
