import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 1. CONFIGURATIE
DATA_DIR = "data"
DB_DIR = "db_mxa"

# De moderne manier om embeddings te laden
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def run_ingestion():
    documenten = []
    
    if not os.path.exists(DATA_DIR):
        print(f"Map {DATA_DIR} bestaat niet.")
        return

    # 2. BESTANDEN LADEN
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documenten.extend(loader.load())
                print(f"Laden van PDF: {filename}")
            elif filename.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                documenten.extend(loader.load())
                print(f"Laden van TXT: {filename}")
        except Exception as e:
            print(f"Fout bij laden van {filename}: {e}")

    if not documenten:
        print("Geen bestanden gevonden in /data.")
        return

    # 3. CHUNKING
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documenten)
    print(f"Tekst opgedeeld in {len(chunks)} stukjes.")

    # 4. OPSLAAN IN DE DATABASE (De nieuwe manier)
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    print(f"✅ Database succesvol aangemaakt in: {DB_DIR}")

if __name__ == "__main__":
    run_ingestion()