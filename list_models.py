"""Kiem tra API key va in ra cac ten model hop le cua key do.

Chay:  venv\\Scripts\\python.exe list_models.py
"""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

for m in client.models.list():
    actions = getattr(m, "supported_actions", []) or []
    if "generateContent" in actions:
        print("CHAT :", m.name)
    if "embedContent" in actions:
        print("EMBED:", m.name)
