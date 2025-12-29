import math
import numpy as np
from config import USE_LOCAL, OPENAI_API_KEY, EMBEDDING_MODEL

# OpenAI client indien nodig
if not USE_LOCAL:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)


def cosine_similarity(vec1, vec2):
    dot = sum(a*b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a*a for a in vec1))
    norm2 = math.sqrt(sum(b*b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)


def top_k_docs(query_embedding, doc_embeddings, docs, k=3):
    scores = [(name, cosine_similarity(query_embedding, emb)) 
              for name, emb in zip(docs.keys(), doc_embeddings)]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:k]


def chunk_text(text, chunk_size=50):
    """Splitst lange tekst in kleinere stukken (default: 50 woorden)"""
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]


def embed_texts(texts, test_mode=False):
    """Genereert embeddings voor een lijst teksten.
    Als test_mode=True → random vectors (geen credits)
    """
    if test_mode:
        return [np.random.rand(10).tolist() for _ in texts]

    if USE_LOCAL:
        # TODO: lokaal model embeddings
        return [np.random.rand(10).tolist() for _ in texts]  # placeholder

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def build_context_from_docs(docs, doc_embeddings, query, k=3, test_mode=False):
    """Selecteert top-K relevante docs en maakt één context string"""
    query_emb = embed_texts([query], test_mode=test_mode)[0]
    top_docs = top_k_docs(query_emb, doc_embeddings, docs, k=k)
    context = "\n".join([f"{name}: {docs[name]}" for name, _ in top_docs])
    return context