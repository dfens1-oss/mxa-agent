import streamlit as st
from groq import Groq
import json

class SemanticRouter:
    def __init__(self):
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model = "llama3-70b-8192"

    def get_route(self, user_query):
        system_prompt = """
        Jij bent de Verkeersleider voor een team van AI experts. Je MOET altijd antwoorden in JSON format.
        
        EXPERTS:
        - carl: Expert in fysieke training, sport en voeding.
        - james: Expert in mentale gezondheid, schaduwwerk en mindset.
        - kevin: Expert in cijfers, logica en administratie (takenlijst).
        - frank: De feiten-checker en overzicht-houder.

        TOOLS:
        - calc: Voor rekensommen. EXPERT MOET 'kevin' ZIJN.
        - voeg_taak_toe: Om iets op een lijst te zetten. EXPERT MOET 'kevin' ZIJN.
        - null: Als er geen actie nodig is, alleen een gesprek.

        REGELS:
        1. "Ik wil sporten" -> expert: carl, tool: null.
        2. "2+2" -> expert: kevin, tool: calc, arguments: {"expressie": "2+2"}.
        3. "Onthou dat ik melk moet kopen" -> expert: kevin, tool: voeg_taak_toe, arguments: {"taak_omschrijving": "Melk kopen"}.

        JSON FORMAT:
        {"expert": "naam", "tool": "tool_naam of null", "arguments": {}}
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Route: {user_query}"}
                ],
                model=self.model,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Router Error: {e}")
            return {"expert": "james", "tool": None, "arguments": {}}