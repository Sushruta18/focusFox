# debug_env.py
from dotenv import load_dotenv
import os

# 1️⃣ Load the .env file
load_dotenv()

# 2️⃣ Try to read the key
api_key = os.getenv("OPENAI_API_KEY")

# 3️⃣ Print it (for debugging only!)
if api_key:
    print("✅ OPENAI_API_KEY loaded successfully:", api_key)
else:
    print("❌ OPENAI_API_KEY not found! Check your .env file")

# 4️⃣ Optional: start FastAPI only if key exists
if api_key:
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/")
    def home():
        return {"message": "FocusFox API running with OpenAI!"}
else:
    print("⚠️ Exiting. Missing API key.")
