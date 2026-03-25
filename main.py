# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
from groq import Groq

import logging

# -------------------- Setup --------------------
# Load .env first
load_dotenv()

# Quick debug: print immediately to confirm key is loaded
api_key_debug = os.getenv("GROQ_API_KEY")
print(f"DEBUG: GROQ_API_KEY loaded: {api_key_debug[:6]}...")  # Only first 6 chars for safety

# Setup logging
logging.basicConfig(level=logging.INFO)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # IMPORTANT
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable for OpenAI client
client = None

# -------------------- Startup Event --------------------
@app.on_event("startup")
def startup_event():
    global client
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing in environment variables")

    logging.info(f"GROQ_API_KEY loaded: {api_key[:6]}...")

    client = Groq(api_key=api_key)


# -------------------- Models --------------------
class TimeEstimate(BaseModel):
    hours: int = 0
    minutes: int = 0

class TaskItem(BaseModel):
    name: str
    estimated_time: Optional[TimeEstimate] = TimeEstimate()
    priority: Optional[str] = "medium"

class TimeAvailable(BaseModel):
    hours: int = 0
    minutes: int = 30

class InputData(BaseModel):
    tasks: List[TaskItem]
    mood: Optional[str] = "neutral"
    time_available: TimeAvailable = TimeAvailable()

class AskInput(BaseModel):
    question: str

# -------------------- Constants --------------------
PRIORITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
MOTIVATIONS = {
    "tired": "Small steps — one tiny win at a time.",
    "stressed": "Breathe. Focus on one small task first.",
    "happy": "Great! Use your energy for a strong focus block!",
    "lazy": "Do just 10 minutes. You can do that.",
    "neutral": "Pick one small, one important task."
}

# -------------------- Helper Function --------------------
def tiny_reorder(tasks: List[TaskItem], mood: str, time_available: TimeAvailable):
    if mood.lower() in ("tired", "stressed", "lazy"):
        tasks = tasks[:3]
    else:
        tasks = tasks[:5]

    if not tasks:
        return []

    total_available = time_available.hours * 60 + time_available.minutes

    weighted_scores = []
    for task in tasks:
        est_min = task.estimated_time.hours * 60 + task.estimated_time.minutes
        if est_min == 0:
            est_min = 5
        p = PRIORITY_WEIGHTS.get(task.priority.lower(), 2)
        weighted_scores.append(est_min * p)

    total_score = sum(weighted_scores)
    plan = []
    for task, score in zip(tasks, weighted_scores):
        allocated_min = round((score / total_score) * total_available)
        h, m = divmod(allocated_min, 60)
        plan.append({"task": task.name, "priority": task.priority, "time": {"hours": h, "minutes": m}})

    return plan

# -------------------- Routes --------------------
@app.get("/")
def home():
    return {"message": "FocusFox API is running!"}

@app.post("/ask")
def ask_ai(data: AskInput):
    if client is None:
        return {"error": "LLM client not initialized"}

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": data.question}
        ]
    )

    answer = response.choices[0].message.content
    return {"answer": answer}

@app.post("/focusfox")
def focusfox(data: InputData):
    logging.info("Received JSON: %s", data.dict())
    mood = (data.mood or "neutral").lower()
    plan = tiny_reorder(data.tasks, mood, data.time_available)
    motivation = MOTIVATIONS.get(mood, MOTIVATIONS["neutral"])
    return {"greeting": f"Here’s a tiny plan for when you’re {mood}:", "plan": plan, "motivation": motivation}
