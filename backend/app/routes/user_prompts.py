
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from app.models import ChatSession, Message, ChatRequest, User, ChatSession_view
from app.dependencies import get_current_user
from app.utils.cloudinary_upload import upload_image_to_cloudinary
import json
from typing import Optional, List

router = APIRouter(prefix="/api/v1/user_prompts", tags=["user_prompts"])

# ---------------------------------------------------------
# 1. GET ALL SESSIONS (Populates the Sidebar)
# ---------------------------------------------------------
@router.get("/sessions")
async def get_user_sessions(
    user: User = Depends(get_current_user) # auth dependency
):
    """
    Fetches the list of chat sessions for the sidebar.
    Returns only metadata (ID, Title, Date) to keep it light.
    """
    # Find sessions by user_id, sort by updated_at (newest first)
    # .project() selects specific fields to reduce bandwidth
    sessions = await ChatSession.find(
        ChatSession.user_id == str(user.id)
    ).sort(
        -ChatSession.updated_at
    ).project(
        ChatSession_view  # You can define a Pydantic view for just these fields(ID, Title, Date)
    ).to_list()
    
    # Or simply return the specific fields:
    return sessions

# ---------------------------------------------------------
# 2. GET SINGLE SESSION (Loads History when clicking Sidebar)
# ---------------------------------------------------------
@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    user: User = Depends(get_current_user)
):
    """
    Loads the full message history for a specific chat session.
    """
    session = await ChatSession.find_one(
        ChatSession.session_id == session_id,
        ChatSession.user_id == str(user.id)
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return session

# ---------------------------------------------------------
# 3. SEND MESSAGE (Handles "New Chat" & "Continue Chat")
# ---------------------------------------------------------
@router.post("/chat")
async def send_message(
    session_id: str = Form(...),
    message: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: User = Depends(get_current_user),
):
    # Normalize
    message = (message or "").strip()
    images = images or []

    if not message and not images:
        raise HTTPException(
            status_code=400,
            detail="Either text message or image is required"
        )

    # Find or create session
    session = await ChatSession.find_one(
        ChatSession.session_id == session_id,
        ChatSession.user_id == str(user.id)
    )

    if not session:
        session = ChatSession(
            user_id=str(user.id),
            session_id=session_id,
            title="New Chat",
            messages=[]
        )
        await session.insert()

    # ---------------- Build content blocks ----------------
    processed_content = []

    # Text first
    if message:
        processed_content.append({
            "type": "text",
            "text": message
        })

    # Images next
    for img in images:
        uploaded_url = await upload_image_to_cloudinary(img)
        processed_content.append({
            "type": "image_url",
            "image_url": {"url": uploaded_url}
        })

    # Create messages
    user_msg = Message(role="user", content=processed_content)

    ai_msg = Message(
        role="assistant",
        content=[{"type": "text", "text": "This is a simulated AI response"}]
    )

    background_tasks.add_task(save_to_mongo, session, user_msg, ai_msg)

    return {"response": ai_msg.content[0].text}



# Background function using Beanie's atomic update
async def save_to_mongo(session: ChatSession, user_msg: Message, ai_msg: Message):

    has_images = any(block.type == "image_url" for block in user_msg.content)

    await session.update(
        {
            "$push": {
                "messages": {
                    "$each": [user_msg.model_dump(), ai_msg.model_dump()]
                }
            }
        },
        {
            "$set": {
                "metadata.has_images": has_images,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if len(session.messages) == 0:
        # trigger_background_title_generator(session.session_id, user_msg, ai_msg)
        pass


# -----------function to export data for fine-tuning -----------
# import json

# def export_for_finetuning(db):
#     # 1. Filter: Get sessions rated highly (good quality data)
#     cursor = db.chat_sessions.find({"metadata.finetune_rating": {"$gte": 4}})
    
#     dataset = []
    
#     for session in cursor:
#         training_entry = {"messages": []}
        
#         for msg in session["messages"]:
#             # OpenAI Fine-tuning strictly accepts: role, content, name
#             # We must strip out 'timestamp', 'vector_id', etc.
            
#             clean_msg = {
#                 "role": msg["role"],
#                 "content": msg["content"]
#             }
#             training_entry["messages"].append(clean_msg)
            
#         dataset.append(training_entry)

#     # 2. Write to JSONL
#     with open("finetune_data.jsonl", "w") as f:
#         for entry in dataset:
#             f.write(json.dumps(entry) + "\n")
            
#     return "finetune_data.jsonl"