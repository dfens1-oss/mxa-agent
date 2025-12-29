import streamlit as st
import json
import os
import ollama
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ---- 0. AI MODEL LADEN (Met cache) ----
@st.cache_resource
def load_embedding_model():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ---- CONFIGURATIE & SETUP ----
load_dotenv()
MODEL_LOCAL = "llama3"
DB_DIR = "db_mxa"

st.set_page_config(page_title="MXA Expert Team", layout="wide")

# Laad het brein
with st.sidebar:
    st.title("MXA Control Center")
    with st.spinner("Brein laden..."):
        embeddings = load_embedding_model()
    st.success("Brein is online ✅")
    
    st.divider()
    st.subheader("Beschikbare Experts")
    st.info("James, Carl, Frank, Kevin, Robert")
    
    # Hier kun je later een afbeelding toevoegen
    # st.image("assets/team_logo.png") 

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ---- 1. KENNIS SYSTEEM (RAG) ----
def get_rag_context(query):
    if not os.path.exists(DB_DIR):
        return "Database niet gevonden."
    try:
        vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
        docs = vector_db.similarity_search(query, k=3)
        return "\n\n".join([f"--- BRON: {d.metadata.get('source')} ---\n{d.page_content}" for d in docs])
    except Exception as e:
        return f"Fout: {e}"

# ---- 2. PERSONA DATA ----
def get_persona_data(persona_name):
    try:
        filename = f"personas/{persona_name.lower()}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"name": persona_name.capitalize(), "catchphrase": "Let's go!"}

# ---- 3. AGENT LOGICA ----
def ask_agent(prompt):
    team = ["carl", "james", "kevin", "robert", "frank"]
    chosen_name = "james" # Default
    
    # Simpele check wie er aangesproken wordt
    for lid in team:
        if lid in prompt.lower():
            chosen_name = lid
            break

    p_data = get_persona_data(chosen_name)
    extra_kennis = get_rag_context(prompt)
    
    full_system_prompt = f"""
    Jij bent {p_data.get('name')}. Antwoord in het Nederlands.
    Catchphrase: {p_data.get('catchphrase')}.
    Gebruik deze context: {extra_kennis}
    """

    response = ollama.chat(model=MODEL_LOCAL, messages=[
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": prompt}
    ])
    return response["message"]["content"], p_data.get("name")

# ---- 4. CHAT INTERFACE ----
st.title("Chat met je MXA Team")

# Toon geschiedenis
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input veld
if prompt := st.chat_input("Stel je vraag..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        antwoord, expert = ask_agent(prompt)
        volledig = f"**{expert}:** {antwoord}"
        st.markdown(volledig)
        st.session_state.messages.append({"role": "assistant", "content": volledig})