import streamlit as st
from groq import Groq
import json

class SemanticRouter:
    def __init__(self):
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model = "llama3-70b-8192"

    def get_route(self, user_query):
        system_prompt = """
        Jij bent de Verkeersleider voor de MXA-app. 
        ANTWOORD ALTIJD IN STRIKT JSON FORMAAT.
        
        EXPERTS:
        - carl: Sport/fysiek.
        - james: Mentaal/schaduwwerk.
        - kevin: Planning/rekenen.
        - frank: Factcheck/snuffelen.
        - robert: Business.

        TOOLS:
        - calc: Voor rekenvragen. Argument: {"equation": "som"}
        - search: Voor zoeken. Argument: {"query": "zoekterm"}
        - null: Als geen tool nodig is.

        OUTPUT JSON STRUCTUUR:
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