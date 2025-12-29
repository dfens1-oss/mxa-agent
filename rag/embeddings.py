from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"

def embed_texts(texts):
    """
    Genereert dummy embeddings van vaste lengte voor testen.
    """
    dim = 1536  # zoals bij OpenAI embeddings
    return [[float(i+j)/dim for j in range(dim)] for i, _ in enumerate(texts)]