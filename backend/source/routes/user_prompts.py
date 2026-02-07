
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, Request
from source.models.user_models import ChatSession, User, ChatSession_view, TextContent, ImageContent, UserTurn, AssistantTurn, ChatTurn, TurnMetadata
from source.dependencies import get_current_user
from source.utils.cloudinary_upload import upload_image_to_cloudinary
from typing import Optional, List
from source.utils.local_embeddings_generator import generate_embedding
from source.utils.get_llm_response import get_llm_response


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
 
   
    try:
        sessions = await ChatSession.find(
        ChatSession.user_id == str(user.id)
        ).sort( 
            -ChatSession.updated_at    
        ).project(                       # .project() selects specific fields to reduce bandwidth
            ChatSession_view             # You can define a Pydantic view for just these fields(ID, Title, Date)
        ).to_list()

        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error", cause=str(e))
    


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
    try:
        session = await ChatSession.find_one(
        ChatSession.session_id == session_id,
        ChatSession.user_id == str(user.id)
        )
    
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error", cause=str(e))
    



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
        cached_result = await semantic_cache.check_cache(embedding)
        print(f"Cache lookup result: {cached_result}")
        if cached_result:
            hit_turn_id = cached_result["turn_id"]
            hit_session_id = cached_result["session_id"]

            # 2. Fetch the ACTUAL text from MongoDB
            # We find the session, and filter for just the specific turn
            cached_session = await ChatSession.find_one(
            ChatSession.session_id == hit_session_id
        )
            # Find the specific turn in the list
            # (Simple Python loop is often faster than complex Mongo queries for small arrays)
            found_text = None
            if cached_session:
                for past_turn in cached_session.turns:
                    if past_turn.turn_id == hit_turn_id:
                        # found it!
                        found_text = past_turn.assistant.content[0].text
                        break
                    
            if found_text:
                # Return cached response

                turn.assistant = AssistantTurn(
                    content=[TextContent(text=found_text)],
                    is_cached=True
                )
                turn.metadata = TurnMetadata(
                    has_images=False,
                    cache_hit=True
                )


                # Save turn asynchronously
                background_tasks.add_task(save_turn_to_mongo, session, turn)

                return {"response": found_text, "cache_used": True, "tokens_used":0}


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
    background_tasks.add_task(save_turn_to_mongo, session, turn, tokens_used)
    if embedding:
        background_tasks.add_task(
        semantic_cache.store_cache,
        embedding,
        turn_id=str(turn.turn_id),
        session_id=session.session_id,
    
    )

    return {"response": ai_text, "cache_used": False, "tokens_used":tokens_used}


# Background function using Beanie's atomic update
async def save_turn_to_mongo(session: ChatSession, turn: ChatTurn, tokens_used: int = 0):
    await session.update(
        {
            "$push": {
                "turns": turn.model_dump()
            }
        },
        {
            "$set": {
                "metadata.has_images": turn.metadata.has_images,
                "metadata.token_usage": session.metadata.get("token_usage", 0) + tokens_used,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    print(f"Turn saved to session {session.session_id}")

    if len(session.turns) == 0:
        # trigger_background_title_generator(session.session_id, user_msg, ai_msg)
        pass

