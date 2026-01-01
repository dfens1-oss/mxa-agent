import streamlit as st
from groq import Groq
import json

class SemanticRouter:
    def __init__(self):
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model = "llama-3.3-70b-versatile"

    def get_route(self, user_query, last_expert=None):
        # We geven de context van de vorige expert mee in de system prompt
        context_instruction = ""
        if last_expert:
            context_instruction = f"De vorige expert die aan het woord was is: '{last_expert}'."

        system_prompt = f"""
        Jij bent de Verkeersleider voor My eXpert Assistent (MXA).
        {context_instruction}

        ### JOUW LOGICA ###
        1. CONTEXT-BEHOUD: Als de gebruiker vraagt "klopt dat?", "is dat zo?" of "echt?", blijf dan bij de expert die als laatste sprak ('{last_expert}'), tenzij er een duidelijke reden is om te wisselen.
        2. HARD RULE: Bij getallen, sommen of rekenkundige tekens (+, -, *, /) kies je ALTIJD 'kevin' en tool 'calc'.
        3. NAAM-PRIORITEIT: Wordt een expert bij naam genoemd? Kies die expert.
        4. James is de expert voor mindset en motivatie. Hij bemoeit zich NOOIT met feiten of cijfers.

        ### EXPERTS ###
        - 'kevin': Cijfers, berekeningen, takenlijsten.
        - 'james': Mindset, reflectie, algemene praat.
        - 'carl': Sport en fysiek.
        - 'robert': Business en carrière.
        - 'frank': Feitencontrole (alleen als de vraag specifiek over de bronnen gaat).

        OUTPUT JSON FORMAT:
        {{"expert": "naam", "tool": "calc" | "voeg_taak_toe" | null, "arguments": {{}}}}
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                model=self.model,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Router Error: {e}") 
            return {"expert": "james", "tool": None, "arguments": {}}