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

def calc(expr):
    import re
    try:
        # Stap 0: Check of er überhaupt getallen in de zin staan
        # Als er geen enkel getal is, is het geen som.
        if not re.search(r'\d', expr):
            return None

        # Stap 1: Schoon de tekst op
        expr_clean = expr.lower().replace(',', '.')
        
        # Stap 2: Zoek alle getallen
        getallen = re.findall(r"\d+\.\d+|\d+", expr_clean)
        
        # Stap 3: BTW / Percentage logica (Blijft hetzelfde)
        if ("btw" in expr_clean or "%" in expr_clean or "procent" in expr_clean) and len(getallen) >= 2:
            perc = float(getallen[0])
            bedrag = float(getallen[1])
            resultaat = (perc / 100) * bedrag
            return round(resultaat, 2)
            
        # Stap 4: Normale som
        # Verwijder tekst. Maar check of er na het verwijderen nog wel iets overblijft om uit te rekenen!
        expr_math = re.sub(r'[a-zA-Z\s\?]', '', expr_clean).strip()
        
        if not expr_math: # Als de zin leeg is na het strippen van letters
            return None
            
        return round(eval(expr_math), 2)
        
    except Exception:
        # Geef None terug bij ELKE fout, zodat mxa.py weet: "Stuur dit maar naar de coaches"
        return None

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
    
    return f"Ik heb het genoteerd: '{taak_omschrijving}'. Check, check, dubbelcheck!"

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