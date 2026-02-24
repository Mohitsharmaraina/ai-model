from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from source.models.user_models import User, Token, RegisterRequest
from config_secrets import settings
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from ..rate_limiting import limiter
from ..dependencies import get_current_user, get_token_from_cookie

router = APIRouter(prefix="/api/v1/user", tags=["users"])

#    hash user password
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def hash_password(plain_password:str) -> str:   
    return pwd_context.hash(plain_password)

# verify password during login
def verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register_user(request:Request, registerRequest: RegisterRequest):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error", cause=str(e))

# @limiter.limit("5/hour")
@router.post("/login")
async def login_user(request:Request, response: Response, form_data:Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await User.find_one(User.email == form_data.username.strip().lower())
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    try:
        # Create JWT Token
        access_token_expires = timedelta(hours=settings.access_token_expire_hours)
        to_encode = {
            "sub": str(user.id),
            "isAdmin": str(user.isAdmin),
            "exp": datetime.now(timezone.utc) + access_token_expires
        }
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        response.set_cookie(key="access_token", value=encoded_jwt, httponly=True, max_age=settings.access_token_expire_hours * 3600)


        return {"success": True, "message": "Login successful", "user": user}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully", "success": True}

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

@router.get("/validate-token")
async def validate_token(token:str = Depends(get_token_from_cookie)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
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
    
    return {"message": "Token is valid", "user": user, "isAdmin": user.isAdmin, "success": True}