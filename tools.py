from gtts import gTTS
import base64
import json
import io
import os
from datetime import datetime

def generate_audio_base64(text):
    """Zet tekst om naar een base64 audio string voor Streamlit"""
    try:
        # We gebruiken 'nl' voor Nederlands
        tts = gTTS(text=text, lang='nl')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Omzetten naar base64 zodat we geen fysiek bestand op de schijf hoeven te beheren
        audio_binary = fp.read()
        audio_base64 = base64.b64encode(audio_binary).decode('utf-8')
        return audio_base64
    except Exception as e:
        print(f"Audio fout: {e}")
        return None

def calculate(*args, **kwargs):
    import re
    try:
        # We kijken of er een waarde in 'args' staat, of in 'kwargs' (onder welke naam dan ook)
        if args:
            equation = args[0]
        elif kwargs:
            # Pak de eerste waarde uit de labels (of dat nu 'expressie', 'equation' of 'som' is)
            equation = list(kwargs.values())[0]
        else:
            return "Geen som gevonden."

        equation_clean = str(equation).replace(',', '.')
        equation_math = re.sub(r'[^0-9\+\-\*\/\.\(\)\s]', '', equation_clean)
        
        if not equation_math.strip():
            return "Geen geldige berekening."
            
        return round(eval(equation_math), 2)
    except Exception as e:
        return f"Berekeningsfout: {e}"

def search(query):
    # Dummy search voor MVP
    return f"Zoekresultaten voor '{query}': [dummy resultaat]"

def file_read(path):
    if not os.path.exists(path):
        return "Bestand bestaat niet."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def file_write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Bestand opgeslagen op {path}"

def voeg_taak_toe(taak_omschrijving):
    """Slaat een nieuwe taak op in het takenlijstje."""
    bestand = 'taken.json'
    tijdstip = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    nieuwe_taak = {
        "datum": tijdstip,
        "taak": taak_omschrijving,
        "status": "open"
    }

    taken = []
    if os.path.exists(bestand):
        with open(bestand, 'r', encoding='utf-8') as f:
            try:
                taken = json.load(f)
            except:
                taken = []

    taken.append(nieuwe_taak)

    with open(bestand, 'w', encoding='utf-8') as f:
        json.dump(taken, f, indent=4, ensure_ascii=False)
    
    return f"Taak genoteerd: '{taak_omschrijving}'." # Catchphrase hier weghalen

def toon_takenlijst():
    """Haalt alle openstaande taken op uit het bestand."""
    bestand = 'taken.json'
    if not os.path.exists(bestand):
        return "Er staan op dit moment geen taken op je lijstje."

    with open(bestand, 'r', encoding='utf-8') as f:
        taken = json.load(f)
    
    if not taken:
        return "Je takenlijst is leeg."

    overzicht = "Hier zijn je huidige taken:\n"
    for i, t in enumerate(taken, 1):
        overzicht += f"{i}. [{t['datum']}] {t['taak']} (Status: {t['status']})\n"
    
    return overzicht