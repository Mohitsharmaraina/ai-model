from typing import Optional, List, Union,  Annotated
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone

from beanie import Document, Indexed


# ------------------------user's model---------------------------------

class RegisterRequest(BaseModel):
    email: Annotated[str, Indexed(unique=True)]
    password: str
    full_name: Optional[str] = None
    model_config = ConfigDict({ 
         "json_schema_extra": {
                "example": {
                    "password": "strongpassword123",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                }
            }
        })

class Token(BaseModel):
    access_token: str
    token_type: str

# ----user model for MongoDB----
class User(Document):
    password: str
    email: Annotated[str, Indexed(unique=True)]
    full_name: Optional[str] = None
    date_joined: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))

    class Settings:
        name = "users"  # Collection name in MongoDB
   

# ------------------------------- Multimodal Content Schemas ------------------------
class TextContent(BaseModel):
    type: str = "text"
    text: str

class ImageUrl(BaseModel):
    url: str  # URL or base64 data

class ImageContent(BaseModel):
    type: str = "image_url"
    image_url: ImageUrl

# A message can be a string OR a list of text/image parts
MessageContent = Union[str, List[Union[TextContent, ImageContent]]]

class ChatRequest(BaseModel):
    session_id: str
    # Input can be simple string or multimodal list
    message: Union[str, List[MessageContent]]
    
class Message(BaseModel):
    role: str # "system", "user", or "assistant"
    content: MessageContent
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_cached: bool = False

class ChatSession_view(BaseModel):
    session_id: str
    title: str
    updated_at: datetime
# --- The Main Collection ---
class ChatSession(Document):
    user_id: Annotated[str, Indexed()] 
    session_id: Annotated[str, Indexed(unique=True)] 
    title: str = "New Chat"  # Default title until AI summarizes it
    
    messages: List[Message] = []
    
    # Timestamps for sorting the sidebar
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    metadata: dict = {
        "quality_score": 0, 
        "has_images": False,
        "is_training_ready": False
    }

    class Settings:
        name = "chat_sessions"
        # Create an index to quickly sort a user's sessions by date
        indexes = [
            [("user_id", 1), ("updated_at", -1)] 
        ]