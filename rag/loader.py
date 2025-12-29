import os

BASE_DIR = os.path.dirname(__file__)
DOCS_DIR = os.path.join(BASE_DIR, "docs")

def load_documents():
    """
    Laadt alle .txt documenten uit rag/docs
    Retourneert een dict: {bestandsnaam: inhoud}
    """
    docs = {}

    if not os.path.exists(DOCS_DIR):
        print(f"⚠️ RAG docs map niet gevonden: {DOCS_DIR}")
        return docs

    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            path = os.path.join(DOCS_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    docs[filename] = f.read()
            except Exception as e:
                print(f"Fout bij lezen van {filename}: {e}")

    if not docs:
        print("⚠️ Geen RAG-documenten gevonden")

    return docs


if __name__ == "__main__":
    documents = load_documents()
    for name, content in documents.items():
        print(f"{name}:\n{content}\n{'-'*40}")