# dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError


# Import your Beanie User model and Settings
from .models import User 
from config import settings

# Define the scheme once here
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")

# This is the DEPENDENCY to get the current user
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
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