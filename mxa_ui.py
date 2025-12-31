import streamlit as st
import os
import json
import base64
import re
import requests
import hashlib
from brain import generate_response, transcribe_audio
from tools import generate_audio_base64, calculate, voeg_taak_toe, toon_takenlijst
from streamlit_mic_recorder import mic_recorder
from router import SemanticRouter

# --- 1. CONFIGURATIE (ALTIJD BOVENAAN) ---
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

# --- 4. DE ZIJKANT (SIDEBAR) ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    
    st.title("MXA Agents")
    
    q = get_daily_quote()
    st.info(f"**Inspiratie:**\n\n*\"{q['quote']}\"* \n\n— {q['author']}")
    
    st.markdown("---")
    st.subheader("Je Expert Team:")
    experts = {
        "James": "Mindset & Algemeen",
        "Kevin": "Cijfers & Planning",
        "Carl": "Sport & Bewegen",
        "Robert": "Business & Carrière",
        "Frank": "Factcheck"
    }
    for naam, rol in experts.items():
        st.write(f"👤 **{naam}**")
        st.caption(rol)
    
    st.markdown("---")
    if st.button("🗑️ Wis geschiedenis"):
        st.session_state.messages = []
        st.session_state.processed_audio_hash = None
        st.rerun()
    st.caption("Check, check, dubbelcheck!")

# --- 5. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_audio_hash" not in st.session_state:
    st.session_state.processed_audio_hash = None

# --- 6. CHAT INTERFACE WEERGAVE ---
st.title("MXA Assistant")

for message in st.session_state.messages:
    role = message["role"]
    p_key = str(message.get("persona", "james")).lower().strip()
    
    # Avatar bepalen
    avatar_data = "👤" if role == "user" else get_image_as_base64(os.path.join(IMAGE_DIR, f"{p_key}.png"))
    if not avatar_data and role != "user":
        icons = {"frank": "🦊", "carl": "💪", "kevin": "📅", "james": "🧠", "robert": "💼"}
        avatar_data = icons.get(p_key, "🤖")

    with st.chat_message(role, avatar=avatar_data):
        st.markdown(message["content"])

# --- 7. INPUT VERWERKING ---
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

# --- 8. HET BREIN (ROUTING & RESPONSE) ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.spinner("Het team overlegt..."):
        route = st.session_state.semantic_router.get_route(last_user_msg)
        chosen_expert = route.get("expert", "james")
        tool_naam = route.get("tool")
        tool_args = route.get("arguments", {})

        extra_info = ""
        if tool_naam == "calc":
            som = list(tool_args.values())[0] if tool_args else last_user_msg
            result = calculate(som)
            extra_info = f"\n(Systeem-notitie: De uitkomst is {result})"
            chosen_expert = "kevin"
        
        elif tool_naam == "voeg_taak_toe":
            taak = list(tool_args.values())[0] if tool_args else "Onbekende taak"
            result = voeg_taak_toe(taak)
            extra_info = f"\n(Systeem-notitie: De taak is opgeslagen. {result})"
            chosen_expert = "kevin"

        response_tekst, persona_name, bronnen = generate_response(last_user_msg + extra_info, chosen_expert)

        persona_slug = re.sub(r'[^a-zA-Z]', '', persona_name).lower().strip()
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_tekst, 
            "persona": persona_slug,
            "display_name": persona_name,
            "bronnen": bronnen
        })
        st.rerun()

# --- 9. AUDIO & BRONNEN ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]
    
    audio_b64 = generate_audio_base64(last_msg["content"])
    if audio_b64:
        audio_html = f'<audio controls autoplay="true" style="width: 100%; height: 35px; margin-top: 10px;"><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)

    if last_msg.get("bronnen"):
        with st.expander("🔍 Bekijk bronnen"):
            for doc in last_msg["bronnen"]:
                p = doc.metadata.get('page', '?')
                st.write(f"**Pagina {p+1 if isinstance(p, int) else p}**")
                st.caption(doc.page_content[:250] + "...")
                st.divider()