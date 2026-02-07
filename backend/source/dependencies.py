# dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from config_secrets import settings


# Import your Beanie User model and Settings
from source.models.user_models import User 
from config_secrets import settings

# Define the scheme once here
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")
oauth2_scheme_super = OAuth2PasswordBearer(tokenUrl="/api/v1/super_admin/login")

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


# get admin user(this method is good if we want to quickly demote admin to common user)

async def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.isAdmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have admin privileges")
    return current_user

# We can implement a Token Blacklist to manually "kill" an admin's session on demotion by super admin
# get admin user (this method is good if we can wait for cookies to expire to change admin status)
# async def get_admin_user(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#     )
#     try:
#         payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
#         # Check the isAdmin flag directly from the token payload
#         is_admin = payload.get("isAdmin")
#         user_id = payload.get("sub")
        
#         if user_id is None:
#             raise credentials_exception
            
#         if not is_admin:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Admin privileges required"
#             )
            
#         return {"user_id": user_id, "isAdmin": is_admin}
        
#     except JWTError:
#         raise credentials_exception

# This is the DEPENDENCY to get the super admin user
async def get_super_admin(token: Annotated[str, Depends(oauth2_scheme_super)]) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        credentials: str = payload.get("sub")
        if credentials is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    

    user = credentials == str(settings.super_admin_email + settings.super_admin_password)
    
    if not user:
        raise credentials_exception
    
    return credentials