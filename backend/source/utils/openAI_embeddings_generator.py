from fastapi import Request

async def generate_embedding(request:Request, text: str) -> list[float]:
    """
    Generates embedding using OpenAI. 
    Reliable, standard, and works with ANY database.
    """
    try:
        client = request.app.state.client
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small" # Efficient and cheap
        
        )
        embedding = response.data[0].embedding
        print("length of generated embedding:",len(embedding))
        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []
