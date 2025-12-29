# rag/store.py
from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ---- Chroma client setup ----
client = Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db",   # map waar vectoren bewaard blijven
    anonymized_telemetry=False          # zet telemetry uit
))

# ---- Embedding functie ----
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
def embedding_fn(texts):
    return embedding_model.encode(texts, convert_to_numpy=True).tolist()

# ---- Collection ophalen of aanmaken ----
try:
    collection = client.get_collection("mxa_collection")
except ValueError:
    collection = client.create_collection(
        name="mxa_collection",
        embedding_function=embedding_fn
    )

def store_text(name: str, text: str, metadata: dict = None):
    """
    Slaat tekst op in de Chroma-collectie.
    metadata: optioneel dict met bijv. {'id': 'doc1'}
    """
    if metadata is None:
        metadata = {"id": name}

    # ids zijn verplicht in nieuwe Chroma-versies
    collection.add(
        ids=[name],              # unieke ID per document
        documents=[text],
        metadatas=[metadata],
    )

def query_docs(user_query: str, n_results: int = 3):
    """
    Zoekt de meest relevante tekstblokken in de database.
    """
    # Deze regels MOETEN ingesprongen zijn met een TAB of 4 spaties
    results = collection.query(
        query_texts=[user_query], 
        n_results=n_results
    )
    
    if results['documents']:
        return results['documents'][0]
    return []