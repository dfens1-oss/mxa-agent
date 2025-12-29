import chromadb
from rag import loader, utils

# ----------------------------
# 1. Laad documenten
# ----------------------------
docs = loader.load_documents()
print("Documenten gevonden:", list(docs.keys())[:5])

# Bekijk één document (eerste 200 tekens)
for name, text in docs.items():
    print(f"\n{name}:\n{text[:200]}...")
    break

texts = list(docs.values())

# ----------------------------
# 2. Dummy embeddings voor lokaal testen
# ----------------------------
def dummy_embed(texts):
    # Maak voor elk document een unieke dummy vector zodat Chroma iets te vergelijken heeft
    return [[float(i)]*1536 for i in range(len(texts))]

embeddings = dummy_embed(texts)
print("Aantal vectoren:", len(embeddings))
print("Eerste vector (5 getallen):", embeddings[0][:5])

# ----------------------------
# 3. Chroma client en collectie
# ----------------------------
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(
    name="local_docs",
    embedding_function=dummy_embed  # Chroma gebruikt dit voor query_texts
)

# Voeg documenten toe (embeddings worden automatisch gebruikt via embedding_function)
collection.add(
    documents=texts,
    ids=list(docs.keys())
)

print("Vector database gevuld met documenten.")

# ----------------------------
# 4. Lokale query testen
# ----------------------------
query = "Wat is MXA?"
results = collection.query(query_texts=[query], n_results=3)

docs_found = results.get("documents", [[]])[0]
print("\nQuery:", query)
print("Gevonden documenten:")
for doc in docs_found:
    print("-", doc[:300], "...")