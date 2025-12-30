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
        You are a routing assistant. You MUST always answer in JSON format.
        Do not include any text outside the JSON object.

        EXPERTS: carl, james, kevin, frank, robert.
        TOOLS: calc, search, null.

        Example output:
        {
          "expert": "kevin",
          "tool": "calc",
          "arguments": {"equation": "2+2"}
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