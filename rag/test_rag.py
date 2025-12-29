# rag/test_rag.py
"""
Testscript voor je RAG functionaliteit:
- Documenten laden
- Embeddings genereren (dummy of echt)
- Cosine similarity en top-k ophalen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # voegt MXA_test toe

from rag.loader import load_documents
from rag.embeddings import embed_texts
from rag.utils import cosine_similarity, top_k_docs, build_context_from_docs

def main():
    print("=== RAG Test gestart ===\n")

    # 1️⃣ Laad alle documenten uit rag/docs
    docs = load_documents()
    if not docs:
        print("Geen documenten gevonden in rag/docs")
        return
    print(f"Gevonden documenten: {list(docs.keys())}\n")

    # 2️⃣ Tekstlijst en embeddings genereren
    texts = list(docs.values())
    print("Genereer embeddings...")
    try:
        embeddings = embed_texts(texts)  # werkt met echte OpenAI embeddings
    except Exception as e:
        print(f"Fout bij embeddings: {e}")
        print("Gebruik dummy embeddings voor test")
        embeddings = [[1.0]*10 for _ in texts]  # dummy vectoren

    # 3️⃣ Cosine similarity testen
    query = "Wat zijn goede routines?"
    print(f"\nQuery: {query}")

    # dummy query embedding
    query_emb = embeddings[0]  # gewoon de eerste als voorbeeld

    top_docs = top_k_docs(query_emb, embeddings, docs, k=2)
    print("\nTop-2 documenten op basis van cosine similarity:")
    for name, score in top_docs:
        print(f"{name}: score {score:.4f}")

    # 4️⃣ Context bouwen voor agent
    context = build_context_from_docs(docs, embeddings, query, k=2)
    print("\nGegenereerde context voor agent:")
    print(context)

    print("\n=== RAG Test afgerond ===")

if __name__ == "__main__":
    main()