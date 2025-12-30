import streamlit as st
from groq import Groq
import json

class SemanticRouter:
    def __init__(self):
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model = "llama3-70b-8192"

    def get_route(self, user_query):
        system_prompt = """
        Jij bent de Verkeersleider voor de MXA-app. Analyseer de vraag en kies de expert en tool.
        
        EXPERTS & LOGICA:
        - carl: Sport, training, oefeningen (trefwoorden: fit, kracht, cardio).
        - james: Mentale gezondheid, schaduwwerk, reflectie.
        - kevin: Planning, agenda en REKENEN.
        - frank: Factchecking, bronnen zoeken, logboek snuffelen.
        - robert: Business en strategie.

        TOOLS:
        - calc: Gebruik dit voor rekenvragen (btw, procent, sommen). 
          ARGUMENT: {"equation": "de pure som zonder woorden"}
        - search: Gebruik dit als er in documenten of bronnen gezocht moet worden.
          ARGUMENT: {"query": "de zoekterm"}

        OUTPUT FORMAAT (Strikt JSON):
        {
          "expert": "naam",
          "tool": "naam_of_null",
          "arguments": {}
        }
        """
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            model=self.model,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)