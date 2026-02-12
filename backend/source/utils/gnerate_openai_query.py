import asyncio
import math

async def get_llm_response(prompt: str) -> dict:
    """
    Simulates an LLM call and returns the response plus token usage.
    """
    # 1. Simulate 2 seconds network delay
    await asyncio.sleep(2) 
    
    # 2. Generate simulated response
    ai_text = f"This is a simulated AI response for query: {prompt}"
    
    # 3. Calculate approximate tokens
    # Calculation: (chars / 4) is a standard approximation for OpenAI/Anthropic
    prompt_tokens = math.ceil(len(prompt) / 4)
    completion_tokens = math.ceil(len(ai_text) / 4)
    total_tokens = prompt_tokens + completion_tokens

    return {
        "answer": ai_text,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
    }

# Example of how to call it:
# result = await get_llm_response("What is corruption?")
# print(f"Tokens used: {result['usage']['total_tokens']}")


async def build_openai_content(user_content):
    content_list = []

    for item in user_content:
        # If it's text
        if hasattr(item, "text"):
            content_list.append({
                "type": "input_text",
                "text": item.text
            })

        # If it's image
        elif hasattr(item, "image_url"):
            content_list.append({
                "type": "input_image",
                "image_url": item.image_url
            })

    return content_list
