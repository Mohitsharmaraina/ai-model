
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, Request
from app.models import ChatSession, User, ChatSession_view, TextContent, ImageContent, UserTurn, AssistantTurn, ChatTurn, TurnMetadata
from app.dependencies import get_current_user
from app.utils.cloudinary_upload import upload_image_to_cloudinary
from typing import Optional, List
from app.utils.semantic_cache import SemanticCache
from app.utils.local_embeddings_generator import generate_embedding
from app.utils.get_llm_response import get_llm_response

# from services.llm import generate_embedding, call_llm

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
    request: Request,
    session_id: str = Form(...),
    message: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: User = Depends(get_current_user),
):
    #pull pre=initialized   cache   from app state
    semantic_cache = request.app.state.semantic_cache
    # ---------------- Normalize ----------------
    message = (message or "").strip()
    images = images or []

    if not message and not images:
        raise HTTPException(
            status_code=400,
            detail="Either text message or image is required"
        )

    # ---------------- Find or create session ----------------
    session = await ChatSession.find_one(
        ChatSession.session_id == session_id,
        ChatSession.user_id == str(user.id)
    )

    if not session:
        session = ChatSession(
            user_id=str(user.id),
            session_id=session_id,
            title="New Chat",
            turns=[]
        )
        await session.insert()

    # ---------------- Build user content ----------------
    user_content = []

    if message:
        user_content.append(TextContent(text=message))

    for img in images:
        uploaded_url = await upload_image_to_cloudinary(img)
        user_content.append(
            ImageContent(image_url=uploaded_url)
        )

    # ---------------- Create Turn ----------------
    turn = ChatTurn(
        user=UserTurn(content=user_content),
        
    )

    # ---------------- Semantic Cache Check for text queries ----------------
    embedding = None
    if (len(images)==0):
        # 1. Generate embedding for the user text message
        embedding = await generate_embedding(message)

        # 2. Check cache
        cached_response = await semantic_cache.check_cache(embedding)
        print(f"Cache lookup result: {cached_response}")
        if cached_response:
            turn.assistant = AssistantTurn(
                content=[TextContent(text=cached_response)],
                is_cached=True
            )
            turn.metadata = TurnMetadata(
                has_images=False,
                cache_hit=True
            )


            # Save turn asynchronously
            background_tasks.add_task(save_turn_to_mongo, session, turn)

            return {"response": cached_response, "cache_used": True, "tokens_used":0}


    # ---------------- Call AI (stubbed) ----------------
    response = await get_llm_response(message or "Image query")
    ai_text = response["answer"]
    tokens_used = response["usage"]["total_tokens"]

    turn.assistant = AssistantTurn(
        content=[TextContent(text=ai_text)],
        is_cached=False
    )
    turn.metadata = TurnMetadata(
        has_images=(len(images) > 0),
        cache_hit=False
    )

    # ---------------- Save async ----------------
    background_tasks.add_task(save_turn_to_mongo, session, turn)
    if embedding:
        background_tasks.add_task(
        semantic_cache.store_cache,
        embedding,
        ai_text,
    
    )

    return {"response": ai_text, "cache_used": False, "tokens_used":tokens_used}


# Background function using Beanie's atomic update
async def save_turn_to_mongo(session: ChatSession, turn: ChatTurn):
    await session.update(
        {
            "$push": {
                "turns": turn.model_dump()
            }
        },
        {
            "$set": {
                "metadata.has_images": turn.metadata.has_images,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    print(f"Turn saved to session {session.session_id}")

    if len(session.turns) == 0:
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