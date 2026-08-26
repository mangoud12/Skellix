"""Secure account registration and login endpoints."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models.user import User
from schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/api", tags=["Authentication"])
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)
settings = get_settings()


def create_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "email": user.email, "exp": expires_at}, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def to_response(user: User) -> AuthResponse:
    return AuthResponse(access_token=create_token(user), user=UserPublic(id=user.id, name=user.name, email=user.email))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    user = User(name=payload.name.strip(), email=email, password_hash=password_context.hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return to_response(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user or not password_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    return to_response(user)


@router.get("/me", response_model=UserPublic)
def me(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> UserPublic:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    try:
        claims = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user = db.get(User, int(claims["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        user = None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    return UserPublic(id=user.id, name=user.name, email=user.email)
