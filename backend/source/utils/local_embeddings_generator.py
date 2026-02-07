from sentence_transformers import SentenceTransformer

model = None

def get_model():
    global model
    if model is None:
        print("Loading SentenceTransformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

async def generate_embedding(text: str) -> list[float]:
    """
    Generates embedding using a local SentenceTransformer model.
    Fast and does not rely on external services.
    """
    try:
        model = get_model()
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


