import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini client
genai.configure(api_key=api_key)

# Pick a model
model = genai.GenerativeModel("gemini-2.0-flash")

# Simple test prompt
response = model.generate_content("Hello Gemini! Can you confirm you are working?")
print(response.text)
