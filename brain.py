import json
import os
import streamlit as st
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DB_DIR = "db_mxa"
PERSONA_DIR = "personas"

# Frank: De centrale verbinding met Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@st.cache_resource
def get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@st.cache_resource
def get_vector_db():
    if not os.path.exists(DB_DIR):
        return None
    try:
        embeddings = get_embeddings()
        return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    except Exception as e:
        st.error(f"Fout bij initialiseren database: {e}")
        return None

def transcribe_audio(audio_bytes):
    try:
        temp_filename = "temp_audio.wav"
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)
        
        with open(temp_filename, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3", 
                file=audio_file
            )
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
        return transcription.text
    except Exception as e:
        return f"Spraakfout: {e}"
    
def get_rag_context(query):
    vector_db = get_vector_db()
    if vector_db is None:
        return "", []
    try:
        docs = vector_db.search(
            query, 
            search_type="mmr", 
            search_kwargs={'k': 8, 'fetch_k': 20, 'lambda_mult': 0.5}
        )
        
        context_items = []
        unique_contents = set()
        sorted_docs = sorted(docs, key=lambda x: x.metadata.get('page', 0))

        for d in sorted_docs:
            content = d.page_content
            if content not in unique_contents:
                page = d.metadata.get('page', '?')
                context_items.append(f"[PAGINA {page}]: {content}")
                unique_contents.add(content)
        
        full_context_text = "\n\n".join(context_items)
        return full_context_text, sorted_docs
    except Exception as e:
        return f"Fout bij zoeken: {e}", []

def get_persona(name):
    try:
        path = os.path.join(PERSONA_DIR, f"{name.lower()}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"name": name.capitalize(), "catchphrase": "Hoppa!", "rules": []}

def generate_response(prompt, expert_name):
    p_data = get_persona(expert_name)
    context_text, bron_documenten = get_rag_context(prompt)
    
    # Frank: De client wordt nu van bovenin hergebruikt!
    
    catchphrase = p_data.get('catchphrase', '')
    rules_str = "\n".join([f"- {r}" for r in p_data.get("rules", [])])    
    
    system_prompt = f"""
    Jij bent {p_data.get('name')}, de {p_data.get('role', 'Expert')}. 
    {p_data.get('description', '')}
    Stijl: {p_data.get('style')}

    ### BELANGRIJKE INSTRUCTIE ###
    - Antwoord ALTIJD in het NEDERLANDS.
    - Vertaal ELK onderdeel uit de context.

    ### CONTEXT ###
    {context_text if context_text else "Geen specifieke bronnen gevonden."}

    ### REGELS ###
    {rules_str}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        antwoord = response.choices[0].message.content.strip()
        
        if catchphrase and catchphrase.lower() not in antwoord.lower():
            antwoord = f"{antwoord}\n\n{catchphrase}"
            
        return antwoord, p_data['name'], bron_documenten
        
    except Exception as e:
        return f"Fout bij Groq: {e}", "Systeem", []