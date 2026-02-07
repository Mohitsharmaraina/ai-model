from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    super_access_token: str
    token_type: str

class GetCurrentUser(BaseModel):
    super_admin_email: str
    full_name: Optional[str] = None

