import streamlit as st
import os
import json
import base64
import re
import requests
import hashlib
from brain import get_mxa_response, transcribe_audio
from tools import generate_audio_base64, calculate, voeg_taak_toe, toon_takenlijst
from streamlit_mic_recorder import mic_recorder
from router import SemanticRouter

# --- 1. CONFIGURATIE ---
st.set_page_config(
    page_title="MXA Expert Flow",
    page_icon="assets/favicon.png",
    layout="centered"
)

# --- 2. INITIALISATIE ---
if 'semantic_router' not in st.session_state:
    st.session_state.semantic_router = SemanticRouter()
IMAGE_DIR = "assets"

# --- 3. HELPER FUNCTIES ---
def get_image_as_base64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None
    return None

def get_daily_quote():
    try:
        res = requests.get("https://zenquotes.io/api/today", timeout=2)
        if res.status_code == 200:
            d = res.json()[0]
            return {"quote": d['q'], "author": d['a']}
    except:
        pass
    return {"quote": "Focus op de horizon.", "author": "James"}

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    
    st.markdown("<h1 style='text-align: center; font-size: 1.2rem; color: #555;'>My eXpert Assistent</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("Team experts")
    experts = {
        "James": "Mindset",
        "Kevin": "Cijfers",
        "Carl": "Sport",
        "Robert": "Business",
        "Frank": "Factcheck"
    }
    
    for naam, rol in experts.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            avatar_path = os.path.join(IMAGE_DIR, f"{naam.lower()}.png")
            if os.path.exists(avatar_path):
                st.image(avatar_path, width=35)
            else:
                st.write("👤")
        with col2:
            st.markdown(f"**{naam}**\n\n<small>{rol}</small>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("🗑️ Wis geschiedenis"):
        st.session_state.messages = []
        st.session_state.processed_audio_hash = None
        st.rerun()
    
    st.caption("Door Maarten")

# --- 5. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_audio_hash" not in st.session_state:
    st.session_state.processed_audio_hash = None

# --- 6. WEERGAVE ---
q = get_daily_quote()
st.caption(f"💡 {q['quote']} — *{q['author']}*")
st.title("My eXpert Assistent")

for message in st.session_state.messages:
    role = message["role"]
    p_key = str(message.get("persona", "james")).lower().strip()
    
    avatar_data = "👤" if role == "user" else get_image_as_base64(os.path.join(IMAGE_DIR, f"{p_key}.png"))
    if not avatar_data and role != "user":
        icons = {"frank": "🦊", "carl": "💪", "kevin": "📅", "james": "🧠", "robert": "💼"}
        avatar_data = icons.get(p_key, "🤖")

    with st.chat_message(role, avatar=avatar_data):
        st.markdown(message["content"])

# --- 7. INPUT ---
audio_data = mic_recorder(start_prompt="🎙️ Praat", stop_prompt="🛑 Stop", key='recorder')
typed_prompt = st.chat_input("Stel je vraag aan het panel...")

if typed_prompt:
    st.session_state.messages.append({"role": "user", "content": typed_prompt})
    st.rerun()

if audio_data and 'bytes' in audio_data:
    current_hash = hashlib.md5(audio_data['bytes']).hexdigest()
    if current_hash != st.session_state.processed_audio_hash:
        with st.spinner("Frank vertaalt je spraak..."):
            tekst = transcribe_audio(audio_data['bytes'])
            if tekst and len(tekst) > 2:
                st.session_state.messages.append({"role": "user", "content": tekst})
                st.session_state.processed_audio_hash = current_hash
                st.rerun()

# --- 8. HET BREIN (DE FLOW) ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.spinner("Het team overlegt..."):
       # Stap A: Bepaal de context en de route
        # We kijken wie als laatste sprak om context-fouten (zoals James die inbreekt) te voorkomen
        last_expert = "james"
        if st.session_state.messages:
            for msg in reversed(st.session_state.messages):
                if msg["role"] == "assistant" and "persona" in msg:
                    last_expert = msg["persona"]
                    break

        route = st.session_state.semantic_router.get_route(last_user_msg, last_expert=last_expert)
        chosen_expert = route.get("expert", "james")
        tool_naam = route.get("tool")
        tool_args = route.get("arguments", {})

        # Stap B: Tool uitvoering & Systeem-notitie (Schoon van triggers!)
        extra_info = ""
        if tool_naam == "calc":
            som = list(tool_args.values())[0] if tool_args else last_user_msg
            result = calculate(som)
            # Frank negeert dit nu omdat we geen 'check' woorden gebruiken
            extra_info = f"\n(Systeem-notitie: Resultaat berekening is {result})"
            chosen_expert = "kevin"
        
        elif tool_naam == "voeg_taak_toe":
            taak = list(tool_args.values())[0] if tool_args else "Onbekende taak"
            result = voeg_taak_toe(taak)
            # Schone systeem-notitie zonder catchphrases
            extra_info = f"\n(Systeem-notitie: De taak is verwerkt in de lijst: {taak})"
            chosen_expert = "kevin"

        # Stap C: Genereer antwoord via Brain
        # We geven beide mee, zodat Kevin de uitkomst weet, maar Frank niet getriggerd wordt
        response_tekst, persona_name, bronnen = get_mxa_response(last_user_msg + extra_info, chosen_expert)

        # ... (Stap D in Sectie 8)
        persona_slug = re.sub(r'[^a-zA-Z]', '', persona_name).lower().strip()
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_tekst, 
            "persona": persona_slug,
            "display_name": persona_name,
            "bronnen": bronnen
        })
        # DIT WAS DE MISSENDE SCHAKEL:
        st.rerun()