import httpx
from fastapi import Depends, HTTPException, Request, status
from clerk_backend_api.security import AuthenticateRequestOptions
from config_secrets import settings


class AuthUser:
    def __init__(self, user_id: str, org_id: str, role: str):
        self.user_id = user_id
        self.org_id = org_id
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_member(self) -> bool:
        return self.role in ["admin", "member"]
    
def convert_to_httpx_request(fastapi_request: Request) -> httpx.Request:
    return httpx.Request(
        method=fastapi_request.method,
        url=str(fastapi_request.url),
        headers=dict(fastapi_request.headers)
    )
    
async def get_current_user(request: Request) -> AuthUser:
    clerk = request.app.state.clerk
    httpx_request = convert_to_httpx_request(request)

    request_state = clerk.authenticate_request(
        httpx_request,
        AuthenticateRequestOptions(
            authorized_parties=[settings.frontend_url]
        )
    )

    if not request_state.is_signed_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    claims = request_state.payload

    user_id = claims.get("sub")
    org_id = claims.get("org_id")
    role = claims.get("org_role") or claims.get("role")
    print("role from clerk", role)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    return AuthUser(
        user_id=user_id,
        org_id=org_id,
        role=role
    )

def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

def require_member(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not user.is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member access required"
        )
    return user