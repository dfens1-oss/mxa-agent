import streamlit as st
from groq import Groq
import json

class SemanticRouter:
    def __init__(self):
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model = "llama-3.3-70b-versatile"

    def get_route(self, user_query):
        system_prompt = """
        Jij bent de Verkeersleider (Dispatcher) voor een team van AI experts. 
        Je enige taak is het analyseren van de gebruikersvraag en de juiste expert en tool selecteren.

        EXPERTS EN HUN DOMEIN:
        1. 'kevin': ALLES wat te maken heeft met getallen, berekeningen, wiskunde, planningen, takenlijsten, agenda's en logistiek.
        2. 'carl': ALLES wat te maken heeft met sport, fitness, oefeningen, beweging en fysieke discipline.
        3. 'frank': Voor kritische feiten-checks of als de gebruiker vraagt om een broncontrole.
        4. 'james': ALLEEN voor mindset, schaduwwerk, filosofie of algemene gesprekken zonder specifiek domein.
        5. 'robert': Zakelijke strategie, carrière-advies, salarisonderhandelingen, marketing en ondernemerschap.

        TOOLS:
        - 'calc': Verplicht bij ELKE rekensom of wiskundige vraag. Expert MOET 'kevin' zijn.
        - 'voeg_taak_toe': Verplicht als de gebruiker iets wil onthouden of op een lijst wil zetten. Expert MOET 'kevin' zijn.
        - null: Als er alleen gesproken wordt zonder toolgebruik.

        STRIKTE OUTPUT REGEL:
        Antwoord uitsluitend in dit JSON format:
        {"expert": "naam", "tool": "tool_naam of null", "arguments": {"expressie": "...", "taak_omschrijving": "..."}}
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query} # 'Route:' weggehaald voor meer puurheid
                ],
                model=self.model,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Hier voegen we een print toe die je in de Streamlit logs kunt zien
            st.error(f"Router Error: {e}") 
            return {"expert": "james", "tool": None, "arguments": {}}