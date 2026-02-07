# import openai
# from config_secrets import settings

# async def generate_embedding(text: str) -> list[float]:
#     """
#     Generates embedding using OpenAI. 
#     Reliable, standard, and works with ANY database.
#     """
#     try:
#         response = await openai.Embedding.acreate(
#             input=text,
#             model="text-embedding-3-small" # Efficient and cheap
#         )
#         return response["data"][0]["embedding"]
#     except Exception as e:
#         print(f"Error generating embedding: {e}")
#         return []
