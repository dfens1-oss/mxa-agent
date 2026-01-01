import json
import os
import streamlit as st
from groq import Groq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from tools import calculate, voeg_taak_toe, toon_takenlijst

DB_DIR = "db_mxa"
PERSONA_DIR = "personas"

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
        # We halen de systeem-notitie weg voor de zoekopdracht in de database
        clean_query = query.split("(Systeem-notitie:")[0]
        docs = vector_db.search(clean_query, search_type="mmr", search_kwargs={'k': 5})
        context_items = []
        unique_contents = set()
        for d in docs:
            if d.page_content not in unique_contents:
                page = d.metadata.get('page', '?')
                context_items.append(f"[PAGINA {page}]: {d.page_content}")
                unique_contents.add(d.page_content)
        return "\n\n".join(context_items), docs
    except Exception as e:
        return f"Fout bij zoeken: {e}", []

def get_persona(name):
    try:
        clean_name = name.lower()
        path = os.path.join(PERSONA_DIR, f"{clean_name}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"name": name.capitalize(), "role": "Expert", "style": "Behulpzaam", "catchphrase": "Check, check, dubbelcheck", "rules": []}

def generate_response(prompt, expert_name):
    p_data = get_persona(expert_name)
    context_text, bron_documenten = get_rag_context(prompt)
    catchphrase = p_data.get('catchphrase', 'Check, check, dubbelcheck')
    rules_str = "\n".join([f"- {r}" for r in p_data.get("rules", [])])
    
    kevin_extra = "Als het om een berekening gaat: geef ENKEL het resultaat. Geen toelichting, geen extra stappen." if expert_name.lower() == "kevin" else ""

    system_prompt = f"""
Jij bent {p_data.get('name')}, de {p_data.get('role', 'Expert')}. 
Stijl: {p_data.get('style')}
{kevin_extra}

### JOUW OPDRACHT ###
- Antwoord in natuurlijk Nederlands.
- Praat direct tegen de gebruiker.
- Eindig ALTIJD met je catchphrase: "{catchphrase}"

### JOUW KENNIS / CONTEXT ###
{context_text}

### JOUW SPECIFIEKE REGELS ###
{rules_str}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        antwoord = response.choices[0].message.content.strip()
        if catchphrase.lower() not in antwoord.lower():
            antwoord = f"{antwoord}\n\n{catchphrase}"
        return antwoord, p_data['name'], bron_documenten
    except Exception as e:
        return f"Fout bij genereren antwoord: {e}", "Systeem", []

def get_mxa_response(full_prompt, expert_name):
    user_part = full_prompt.split("(Systeem-notitie:")[0].lower()
    trigger_woorden = ["factcheck", "klopt dat", "controleer dit", "bevestig dit", "klopt dit"]
    vraagt_om_check = any(word in user_part for word in trigger_woorden)

    if vraagt_om_check:
        # We halen de laatste 2 berichten op uit de geschiedenis voor Frank
        history_context = ""
        if "messages" in st.session_state and len(st.session_state.messages) >= 1:
            # Pak de laatste paar berichten om context te geven
            last_msgs = st.session_state.messages[-3:] 
            history_context = "\n".join([f"{m['role']}: {m['content']}" for m in last_msgs])

        context_voor_frank = f"""
        De gebruiker twijfelt aan het vorige antwoord. 
        HIER IS DE RECENTE GESCHIEDENIS:
        {history_context}

        Beoordeel of het laatste antwoord van de assistent feitelijk of wiskundig correct is.
        """
        # We sturen de geschiedenis direct mee in de prompt naar Frank
        frank_antwoord, persona_name, bronnen = generate_response(f"{context_voor_frank}\n\nVraag van gebruiker: {full_prompt}", "frank")
        return frank_antwoord, "Frank", bronnen

    # Normale flow
    return generate_response(full_prompt, expert_name)