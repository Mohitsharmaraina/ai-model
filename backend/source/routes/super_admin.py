from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from source.models.super_admin_model import Token
from source.models.user_models import User
from source.dependencies import get_super_admin
from config_secrets import settings
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from beanie import PydanticObjectId

router = APIRouter(prefix="/api/v1/super_admin", tags=["super_admin"])


@router.post("/login", response_model=Token,)
async def super_admin_login( response: Response, form_data:Annotated[OAuth2PasswordRequestForm, Depends()]):

    valid_email = settings.super_admin_email == form_data.username.strip().lower()
    valid_password = settings.super_admin_password == form_data.password
    
    if not valid_email or not valid_password:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    try:
        # Create JWT Token
        access_token_expires = timedelta(hours=settings.access_token_expire_hours)
        to_encode = {
            "sub": str(settings.super_admin_email + settings.super_admin_password),
            "exp": datetime.now(timezone.utc) + access_token_expires
        }
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        response.set_cookie(key="super_access_token", value=encoded_jwt, httponly=True, max_age=settings.access_token_expire_hours * 3600)

        return {"super_access_token": encoded_jwt, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

@router.get("/getAllUsers", response_model=list[User])
async def get_all_users(credentials: Annotated[str, Depends(get_super_admin)]):
   
    try:
        users = await User.find_all().to_list()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error", cause=str(e))
    

@router.put("/updateUser", response_model=User)
async def update_user(userId: PydanticObjectId, credentials: Annotated[str, Depends(get_super_admin)]):
   
    try:
        user = await User.get(userId)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.isAdmin = not user.isAdmin
        await user.save()
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error", cause=str(e))
    