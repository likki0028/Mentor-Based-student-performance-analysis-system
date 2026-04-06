import os
import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print("ERROR:", e)
