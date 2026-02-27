
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, Request
from openai import OpenAIError
from source.models.user_models import ChatSession, User, ChatSession_view, TextContent, ImageContent, UserTurn, AssistantTurn, ChatTurn, TurnMetadata, TitleUpdate
from source.dependencies import get_current_user, get_token_from_cookie
from source.utils.s3_upload import upload_to_s3
from typing import Optional, List
from source.utils.local_embeddings_generator import generate_embedding
# from source.utils.openAI_embeddings_generator import generate_embedding
from source.utils.gnerate_openai_query import build_openai_content, get_llm_response
import logging


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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    


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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    

# ---------------------------------------------------------
# 3. UPDATE SINGLE SESSION (Updates Title when user changes it)
# ---------------------------------------------------------
@router.put("/sessions/{session_id}")
async def update_session_title(
    session_id: str,
    title_update: TitleUpdate,
    user: User = Depends(get_current_user)
):
    """
    Updates the title of a specific chat session.
    """
    try:
        session = await ChatSession.find_one(
            ChatSession.session_id == session_id,
            ChatSession.user_id == str(user.id)
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update the title
        session.title = title_update.title
        await session.save()

        return {"message": "Session title updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ---------------------------------------------------------
# 4. SEND MESSAGE (Handles "New Chat" & "Continue Chat")
# ---------------------------------------------------------

def is_cacheable_query(query, response):
    words = query.split()
    if len(words) < 6:
        return False
    # if len(response.split()) < 30:
    #     return False
    skip_words = ["hi", "hello", "thanks", "ok"]
    if query.lower().strip() in skip_words:
        return False
    return True

@router.post("/chat")
async def send_message(
    request: Request,
    session_id: str = Form(...),
    message:str = Form(...),
    web_search: Optional[bool] = Form(False),
    # images: Optional[List[UploadFile]] = File(None),
    images: Optional[List[UploadFile]] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: User = Depends(get_current_user),
):
    print("web search value:", web_search, "type:", type(web_search)) 
    #pull pre=initialized   cache   from app state
    semantic_cache = request.app.state.semantic_cache
    # ---------------- Normalize ----------------
    message = (message or "").strip()
    images = images or []

    if not message and not images:
        raise HTTPException(
            status_code=400,
            detail="Type your query response first."
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
        if(len(images)>1):
            raise HTTPException(
                status_code= 400,
                detail="Only one image per query is supported"
            )
        uploaded_url = await upload_to_s3(request ,img)
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
        # 1. --------------------------------Generate embedding for the user text message--------------------------------
        # embedding = await generate_embedding(request, message)     ----> for openai embedding generator

        # -local embedding generator model-
        embedding = await generate_embedding(message)

        # 2. ------------------------Check cache------------------------
        cached_result = await semantic_cache.check_cache(embedding)
        print(f"Cache lookup result: {cached_result}")
        if cached_result:
            hit_turn_id = cached_result["turn_id"]
            hit_session_id = cached_result["session_id"]

            # Fetch the ACTUAL text from MongoDB
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

                return {"response": found_text, "cache_used": True, "tokens_used":0, "image_urls": []}


    # ---------------- Call openAI Model ----------------

    # 1. initialize client 
    client = request.app.state.client

    # 2. generate model context using previous messages
    MAX_HISTORY_TURNS = 2
    recent_turns = session.turns[-MAX_HISTORY_TURNS:]

    openai_messages = []

    # Add system via instructions (cleaner)
    instructions = '''You are PZWInd AI Chatbot.'''

    # Add history
    for past_turn in recent_turns:
        openai_messages.append({
            "role": "user",
            "content": await build_openai_content(past_turn.user.content[0].text)
        })
        openai_messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": past_turn.assistant.content[0].text
                }
            ]
        })
    openai_content =await build_openai_content(user_content)

    # Add current user message
    openai_messages.append({
        "role": "user",
        "content": openai_content
    })

    if web_search:
        instructions += """
                        If web search is used:
                        - Prefer authoritative sources
                        - Cross-check information if possible
                        - Mention uncertainty when information conflicts
                        - Do not fabricate missing facts
                        - Clearly indicate if data may be outdated
                        """
        tools = [
            {"type": "web_search"}
        ]

   
    try:
        response = client.responses.create(
        model="ft:gpt-4o-2024-08-06:personal::DDmJLoWY",
        # model="gpt-4o-2024-08-06",
        instructions=instructions,
        input=openai_messages,
        temperature=0.7,
        max_output_tokens = 5000,
        tools=tools if web_search else None
        )
    except OpenAIError as e:
        logging.exception("OpenAI API error: %s", str(e))
        raise HTTPException(status_code=502, detail="Error communicating with AI service")
    except Exception as e:
        logging.exception("Unexpected error :", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
     

    ai_text = ""
    citations = []

    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    ai_text += content.text

                if hasattr(content, "annotations") and content.annotations:
                    for ann in content.annotations:
                        if ann.type == "url_citation":
                            citations.append({
                                "title": ann.title,
                                "url": ann.url
                            })
    tokens_used = response.usage.total_tokens
    # input_tokens = response.usage.input_tokens
    # output_tokens = response.usage.output_tokens

    # response = await get_llm_response(message or "Image query")
    # ai_text = response["answer"]
    # tokens_used = response["usage"]["total_tokens"]

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
        if is_cacheable_query(message, ai_text):
            background_tasks.add_task(
            semantic_cache.store_cache,
            embedding,
            turn_id=str(turn.turn_id),
            session_id=session.session_id,
    
        )

    return {"response": ai_text, "citations": citations, "web_search_used": len(citations)>0,"cache_used": False, "tokens_used":tokens_used, "image_urls":[img.image_url for img in user_content if isinstance(img, ImageContent)], }


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

    # if len(session.turns) == 0:
    #     # trigger_background_title_generator(session.session_id, user_msg, ai_msg)
    #     pass

