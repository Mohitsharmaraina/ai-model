
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.models import ChatSession, Message, ChatRequest, User, ChatSession_view
from app.dependencies import get_current_user


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
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Main chat endpoint.
    1. Checks if session exists. If not, creates it (New Chat).
    2. Checks Vector DB for Semantic Cache (Stubbed here).
    3. Generates AI Response (Stubbed here).
    4. returns AI Response immediately.
    5. Saves AI Response & User Message.
    6. Updates 'updated_at' so it jumps to top of sidebar.
    """
    
    # 1. Try to find the session
    session = await ChatSession.find_one(
        ChatSession.session_id == payload.session_id,
        ChatSession.user_id == str(user.id)
    )

    # 2. If "New Chat", create the session document
    if not session:
        session = ChatSession(
            user_id=str(user.id),
            session_id=payload.session_id,
            title="New Chat", # update this later with AI summarization
            messages=[]
        )
        await session.insert()

    # 3. Create User Message Object
    user_msg = Message(
        role="user",
        content=payload.message
    )
    # 2. Check Vector DB for Semantic Cache (Text queries only)
    # ... (cache logic here) ...

    # 3. Call GPT-4o (using session.messages for context)
    # response_text = call_gpt4o(request.message, session.messages)
    
    ai_response_text = f"This is a simulated AI response for {user_msg.content}"  # Stubbed response
    # --------------------------

    ai_msg = Message(
        role="assistant",
        content=ai_response_text
    )
        # 4. Background Task: Atomic Update to MongoDB
    background_tasks.add_task(
        save_to_mongo, 
        session, 
        user_msg, 
        ai_msg
    )

    return {"response": ai_response_text}


# Background function using Beanie's atomic update
async def save_to_mongo(session: ChatSession, user_msg, ai_msg):
    # Check if input had images for metadata
    has_images = any(isinstance(i, dict) and i.get("type") == "image_url" for i in user_msg.content) if isinstance(user_msg.content, list) else False

    # Atomic push to avoid race conditions
    await session.update(
        {"$push": {"messages": {"$each": [user_msg.model_dump(), ai_msg.model_dump()]}}},
        {"$set": {"metadata.has_images": has_images,"updated_at": datetime.now(timezone.utc)} }
        
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