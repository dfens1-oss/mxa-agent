import streamlit as st
import os
import json
import random
import base64
import re
import requests
from datetime import date
from brain import generate_response
from tool_router import route_expert, detect_tool
from tools import generate_audio_base64
from streamlit_mic_recorder import mic_recorder

# --- CONFIGURATIE & PADEN ---
st.set_page_config(page_title="MXA Assistant", page_icon="🦁", layout="centered")
IMAGE_DIR = "assets"

# --- HELPER FUNCTIE (Voor de PNG avatars) ---
def get_image_as_base64(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None
    return None

# --- QUOTE FUNCTIE ---
def get_daily_quote():
    try:
        # We roepen een gratis API aan die de 'Quote of the Day' geeft
        response = requests.get("https://zenquotes.io/api/today", timeout=5)
        if response.status_code == 200:
            data = response.json()[0]
            return {
                "quote": data['q'],
                "author": data['a'],
                "persona": "Inspiratie"
            }
    except Exception as e:
        # Als het internet even weg is, gebruiken we een veilige fallback
        pass
    
    return {
        "quote": "Focus op de horizon.", 
        "author": "James", 
        "persona": "James"
    }

# --- SIDEBAR DISPLAY ---
personas_display = {
    "James": {"img": os.path.join(IMAGE_DIR, "james.png"), "caption": "James"},
    "Carl": {"img": os.path.join(IMAGE_DIR, "carl.png"), "caption": "Carl"},
    "Kevin": {"img": os.path.join(IMAGE_DIR, "kevin.png"), "caption": "Kevin"},
    "Robert": {"img": os.path.join(IMAGE_DIR, "robert.png"), "caption": "Robert"},
    "Frank": {"img": os.path.join(IMAGE_DIR, "frank.png"), "caption": "Frank"}
}

with st.sidebar:
    main_avatar = os.path.join(IMAGE_DIR, "james.png")
    if os.path.exists(main_avatar):
        st.image(main_avatar, width=100)
    
    st.markdown("### Je AI Coach Team")
    q = get_daily_quote()
    st.info(f"**{q['persona']} zegt:**\n\n*\"{q['quote']}\"* \n\n— {q['author']}")
    
    if st.button("🗑️ Wis geschiedenis"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.header("Het Team")
    for p_name, p_info in personas_display.items():
        if os.path.exists(p_info["img"]):
            st.image(p_info["img"], width=80, caption=p_info["caption"])

# --- CHAT INTERFACE ---
st.title("MXA Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Weergave van geschiedenis
for message in st.session_state.messages:
    role = message["role"]
    p_key = str(message.get("persona", "james")).lower().strip()
    avatar_data = "👤" if role == "user" else get_image_as_base64(os.path.join(IMAGE_DIR, f"{p_key}.png"))
    
    if not avatar_data and role != "user":
        icons = {"frank": "🦊", "carl": "💪", "kevin": "📅", "james": "🧠", "robert": "💼"}
        avatar_data = icons.get(p_key, "🤖")

    with st.chat_message(role, avatar=avatar_data):
        st.markdown(message["content"])

# --- INPUT & VERWERKING ---
st.write("---")
col_mic, col_spacer = st.columns([0.2, 0.8])
with col_mic:
    audio_data = mic_recorder(
        start_prompt="🎙️ Praat",
        stop_prompt="🛑 Stop",
        key="mic_recorder"
    )

typed_prompt = st.chat_input("Stel je vraag aan het panel...")

prompt = None
if audio_data and audio_data.get('transcription'):
    prompt = audio_data['transcription']
elif typed_prompt:
    prompt = typed_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.spinner("Het team overlegt..."):
        # 1. Bepaal de expert
        expert_from_router = route_expert(prompt)
        
        if expert_from_router:
            chosen_expert = expert_from_router
        elif len(st.session_state.messages) > 1:
            last_assistant_msg = next((m for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
            chosen_expert = last_assistant_msg.get("persona", "james") if last_assistant_msg else "james"
        else:
            chosen_expert = "james"

        # 2. Logica voor antwoord genereren
        bronnen = []
        tool_call = detect_tool(prompt)
        
        if tool_call and tool_call["tool"] == "calc":
            try:
                from tools import calc
                res = calc(**tool_call["args"])
                response_tekst, persona_display_name = f"Ik heb het uitgerekend: {res}", "Kevin"
            except Exception:
                response_tekst, persona_display_name = "Er ging iets mis bij het rekenen.", "Kevin"
        else:
            response_tekst, persona_display_name, bronnen = generate_response(prompt, chosen_expert)

        # 4. Avatar logica bepalen
        active_persona_slug = re.sub(r'[^a-zA-Z]', '', persona_display_name).lower().strip()
        final_avatar = get_image_as_base64(os.path.join(IMAGE_DIR, f"{active_persona_slug}.png"))
        if not final_avatar:
            icons = {"frank": "🦊", "carl": "💪", "kevin": "📅", "robert": "💼"}
            final_avatar = icons.get(active_persona_slug, "🤖")

        # 5. EENMALIGE weergave in de chat
        with st.chat_message("assistant", avatar=final_avatar):
            st.markdown(f"**{persona_display_name}**")
            st.write(response_tekst)

            audio_b64 = generate_audio_base64(response_tekst)
            if audio_b64:
                audio_html = f"""
                    <audio controls autoplay="true" style="width: 100%; height: 35px; margin-top: 10px;">
                        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)

            if bronnen:
                with st.expander("🔍 Bekijk bronnen (vossig speurwerk)"):
                    for doc in bronnen:
                        p = doc.metadata.get('page', '?')
                        p_display = p + 1 if isinstance(p, int) else p
                        st.write(f"**Pagina {p_display}**")
                        st.caption(doc.page_content[:250] + "...")
                        st.divider()

        # 6. Opslaan in historie (Nu correct ingesprongen)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"**{persona_display_name}:** {response_tekst}", 
            "persona": active_persona_slug
        })