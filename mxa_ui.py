import streamlit as st
import os
import json
import random
import base64
import re
import requests
import hashlib
from datetime import date
from brain import generate_response, transcribe_audio
from tools import generate_audio_base64
from streamlit_mic_recorder import mic_recorder
from router import SemanticRouter
semantic_router = SemanticRouter()

# --- CONFIGURATIE & PADEN ---
st.set_page_config(page_title="MXA Assistant", page_icon="🦁", layout="centered")
IMAGE_DIR = "assets"

# --- INITIALISATIE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_audio_hash" not in st.session_state:
    st.session_state.processed_audio_hash = None

# --- HELPER FUNCTIE ---
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
        response = requests.get("https://zenquotes.io/api/today", timeout=5)
        if response.status_code == 200:
            data = response.json()[0]
            return {"quote": data['q'], "author": data['a'], "persona": "Inspiratie"}
    except Exception:
        pass
    return {"quote": "Focus op de horizon.", "author": "James", "persona": "James"}

# --- SIDEBAR ---
with st.sidebar:
    main_avatar = os.path.join(IMAGE_DIR, "james.png")
    if os.path.exists(main_avatar):
        st.image(main_avatar, width=100)
    
    st.markdown("### Je AI Coach Team")
    q = get_daily_quote()
    st.info(f"**{q['persona']} zegt:**\n\n*\"{q['quote']}\"* \n\n— {q['author']}")
    
    if st.button("🗑️ Wis geschiedenis"):
        st.session_state.messages = []
        st.session_state.processed_audio_hash = None
        st.rerun()

# --- CHAT INTERFACE WEERGAVE ---
st.title("MXA Assistant")

for message in st.session_state.messages:
    role = message["role"]
    p_key = str(message.get("persona", "james")).lower().strip()
    avatar_data = "👤" if role == "user" else get_image_as_base64(os.path.join(IMAGE_DIR, f"{p_key}.png"))
    
    if not avatar_data and role != "user":
        icons = {"frank": "🦊", "carl": "💪", "kevin": "📅", "james": "🧠", "robert": "💼"}
        avatar_data = icons.get(p_key, "🤖")

    with st.chat_message(role, avatar=avatar_data):
        st.markdown(message["content"])

# --- AUDIO INPUT & VERWERKING (De Loop Fix) ---
audio_data = mic_recorder(start_prompt="🎙️ Praat", stop_prompt="🛑 Stop", key='recorder')

prompt = None

if audio_data and 'bytes' in audio_data:
    # Maak een unieke hash van de audio bytes
    current_audio_hash = hashlib.md5(audio_data['bytes']).hexdigest()
    
    # Check of we deze audio al verwerkt hebben
    if current_audio_hash != st.session_state.processed_audio_hash:
        with st.spinner("Frank vertaalt je spraak..."):
            tekst_van_spraak = transcribe_audio(audio_data['bytes'])
            
            if tekst_van_spraak and len(tekst_van_spraak) > 2:
                st.session_state.messages.append({"role": "user", "content": tekst_van_spraak})
                st.session_state.processed_audio_hash = current_audio_hash
                st.rerun()

# --- TEXT INPUT ---
typed_prompt = st.chat_input("Stel je vraag aan het panel...")
if typed_prompt:
    prompt = typed_prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- ANTWOORD GENEREREN ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]
    
    with st.spinner("Het team overlegt..."):
        # 1. De Nieuwe Semantische Router aanroepen
        route = semantic_router.get_route(last_user_msg)
        chosen_expert = route["expert"]
        tool_naam = route["tool"]
        tool_args = route.get("arguments", {})

        # 2. Check of er een tool uitgevoerd moet worden
        tool_result = None
        if tool_naam == "calc":
            from tools import calculate
            
            # We pakken de waarde uit de dictionary, ongeacht de naam (expressie/equation)
            if isinstance(tool_args, dict) and tool_args:
                # Dit pakt de allereerste waarde uit de verzameling argumenten
                args_list = list(tool_args.values())
                equation_to_solve = args_list[0]
            else:
                equation_to_solve = last_user_msg

            # CRUCIAAL: We geven de waarde door zonder 'keyword' (dus niet equation=...)
            # Hierdoor accepteert de functie het altijd.
            tool_result = calculate(equation_to_solve)
            
            last_user_msg = f"{last_user_msg} (Systeem-notitie voor Kevin: De uitkomst is {tool_result})"

        # 3. Genereer response via Brain (met de gekozen expert)
        response_tekst, persona_display_name, bronnen = generate_response(last_user_msg, chosen_expert)

        # 4. Sla op in history
        active_persona_slug = re.sub(r'[^a-zA-Z]', '', persona_display_name).lower().strip()
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_tekst, 
            "persona": active_persona_slug,
            "display_name": persona_display_name,
            "bronnen": bronnen
        })
        st.rerun()

# --- AUDIO & BRONNEN WEERGAVE (Voor het laatste bericht) ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]
    
    # Audio afspelen voor het nieuwste bericht
    audio_b64 = generate_audio_base64(last_msg["content"])
    if audio_b64:
        audio_html = f"""
            <audio controls autoplay="true" style="width: 100%; height: 35px; margin-top: 10px;">
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

    # Bronnen tonen
    if last_msg.get("bronnen"):
        with st.expander("🔍 Bekijk bronnen (vossig speurwerk)"):
            for doc in last_msg["bronnen"]:
                p = doc.metadata.get('page', '?')
                st.write(f"**Pagina {p+1 if isinstance(p, int) else p}**")
                st.caption(doc.page_content[:250] + "...")
                st.divider()