import streamlit as st
from groq import Groq
import json

class SemanticRouter:
    def __init__(self):
        # Check, check, dubbelcheck: Staat je API key goed in Streamlit Secrets?
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model = "llama3-70b-8192"

    def get_route(self, user_query):
        system_prompt = """
        Jij bent de Verkeersleider. Je MOET altijd antwoorden in JSON format.
        
        EXPERTS:
        - carl: Fysiek, sport, voeding.
        - james: Mentaal, schaduwwerk, mindset.
        - kevin: Cijfers, logica, techniek.
        - frank: Factchecker, overzicht.
        - robert: (Indien van toepassing).

        TOOLS (Gebruik deze ALLEEN bij directe opdrachten):
        - calc: Gebruik dit ALLEEN als er een rekensom moet worden opgelost.
        - voeg_taak_toe: Gebruik dit ALLEEN als de gebruiker vraagt om iets te onthouden of te noteren.
        - null: Gebruik dit als er GEEN tool nodig is en de gebruiker gewoon wil praten.

        BELANGRIJKE REGEL:
        Als de gebruiker een wens uitspreekt (bijv. "ik wil sporten"), stuur hem dan naar de expert met tool "null". 
        Roep een tool ALLEEN aan als er een actie wordt gevraagd (bijv. "Reken uit..." of "Zet dit op mijn lijst").

        Output Format:
        {
          "expert": "naam",
          "tool": "tool_naam of null",
          "arguments": {"equation": "waarde" of "taak": "waarde"}
        }
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    # We herhalen hier expliciet dat de user JSON wil
                    {"role": "user", "content": f"Route this query and provide JSON output: {user_query}"}
                ],
                model=self.model,
                # Dit dwingt de API naar JSON-modus
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Fallback als Groq echt weigert, zodat je app niet crasht
            print(f"Router Error: {e}")
            return {"expert": "james", "tool": None, "arguments": {}}