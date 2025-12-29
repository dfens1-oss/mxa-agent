import re

def detect_tool(prompt):
    """Detecteert of er een technische actie (rekenen/lezen) nodig is."""
    p = prompt.strip().lower()

    # ---- 1. REKENEN ----
    reken_trefwoorden = ["btw", "procent", "%", "reken", "bereken", "som"]
    if any(woord in p for woord in reken_trefwoorden) or re.match(r'^[0-9\s\+\-\*\/\(\)\.]+$', p):
        expr = p.replace("bereken", "").replace("reken", "").strip()
        return {"tool": "calc", "args": {"expr": expr}}

    # ---- 2. ZOEKEN ----
    if p.startswith("zoek") or "zoeken naar" in p:
        query = p.replace("zoek", "").replace("zoeken naar", "").strip()
        return {"tool": "search", "args": {"query": query}}

    return None

def route_expert(prompt):
    """Bepaalt welke persoon (James, Carl, etc.) het antwoord moet geven."""
    p_low = prompt.lower()
    
    # 1. Directe namen (hoogste prioriteit)
    if "carl" in p_low: return "carl"
    if "james" in p_low: return "james"
    if "frank" in p_low: return "frank"
    if "kevin" in p_low: return "kevin"
    if "robert" in p_low: return "robert"

    # 2. Trefwoorden (onderwerp-herkenning)
    # Carl: Fysieke actie
    if any(w in p_low for w in ["sport", "train", "oefening", "rug", "kracht", "cardio", "fit"]):
        return "carl"
    
    # Kevin: Rekenen EN Agenda (NU AANGEVULD)
    if any(w in p_low for w in ["reken", "btw", "euro", "procent", "som", "hoeveel is", "agenda", "afspraak", "plannen", "kalender", "wanneer"]):
        return "kevin"
    
    # Frank: Feiten en Documenten
    if any(w in p_low for w in ["klopt dit", "feit", "check", "bron", "waarheid", "onderzoek", "document", "snuffel"]):
        return "frank"

    return None