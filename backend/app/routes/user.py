from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from app.models import User, Token, RegisterRequest
from config_secrets import settings
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError

router = APIRouter(prefix="/api/v1/user", tags=["users"])

#    hash user password
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def hash_password(plain_password:str) -> str:
    
    return pwd_context.hash(plain_password)

# verify password during login
def verify_password(plain_password:str, hashed_password:str) -> bool:

    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(registerRequest: RegisterRequest):
    try:
       user = User(
           email=registerRequest.email.strip().lower(),
           password=hash_password(registerRequest.password),
           full_name=registerRequest.full_name
       )
       await user.insert()
       return {"message": "User registered successfully"}   
   
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")

@router.post("/login", response_model=Token,)
async def login_user( response: Response, form_data:Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await User.find_one(User.email == form_data.username.strip().lower())
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    # Create JWT Token
    access_token_expires = timedelta(hours=settings.access_token_expire_hours)
    to_encode = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) + access_token_expires
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    response.set_cookie(key="access_token", value=encoded_jwt, httponly=True, max_age=settings.access_token_expire_hours * 3600)
    response.set_cookie(key="userId", value=str(user.id), httponly=True, max_age=settings.access_token_expire_hours * 3600)

    return {"access_token": encoded_jwt, "token_type": "bearer"}

@router.get("/getUser", response_model=User)
async def get_current_user(token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/user/login"))]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await User.get(user_id)
    if user is None:
        raise credentials_exception
    
    return user