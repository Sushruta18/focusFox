# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], )

class TimeEstimate(BaseModel):
    hours: int = 0
    minutes: int = 0

class TaskItem(BaseModel):
    name: str
    estimated_time: Optional[TimeEstimate] = TimeEstimate() 
    priority: Optional[str] = "medium"

PRIORITY_WEIGHTS = {
    "high": 3,
    "medium": 2,
    "low": 1
}

class TimeAvailable(BaseModel):
    hours: int = 0
    minutes: int = 30

class InputData(BaseModel):
    tasks: List[TaskItem]
    mood: Optional[str] = "neutral"
    time_available: TimeAvailable = TimeAvailable()


# --------- Motivation dictionary ---------
MOTIVATIONS = {
    "tired": "Small steps — one tiny win at a time.",
    "stressed": "Breathe. Focus on one small task first.",
    "happy": "Great! Use your energy for a strong focus block!",
    "lazy": "Do just 10 minutes. You can do that.",
    "neutral": "Pick one small, one important task."
}

# --------- Tiny task reordering + time division ---------
def tiny_reorder(tasks: List[TaskItem], mood: str, time_available: TimeAvailable):

    # 1. Mood-based limit
    if mood.lower() in ("tired", "stressed", "lazy"):
        tasks = tasks[:3]
    else:
        tasks = tasks[:5]

    if not tasks:
        return []

    # 2. Convert available time → minutes
    total_available = time_available.hours * 60 + time_available.minutes

    # 3. Compute weighted scores for each task
    weighted_scores = []
    for task in tasks:
        est_min = task.estimated_time.hours * 60 + task.estimated_time.minutes
        if est_min == 0:
            est_min = 5

        # Priority weight
        p = PRIORITY_WEIGHTS.get(task.priority.lower(), 2)

        score = est_min * p
        weighted_scores.append(score)

    total_score = sum(weighted_scores)

    # 4. Allocate time proportionally using weighted scores
    plan = []
    for task, score in zip(tasks, weighted_scores):
        allocated_min = round((score / total_score) * total_available)
        h, m = divmod(allocated_min, 60)

        plan.append({
            "task": task.name,
            "priority": task.priority,
            "time": {"hours": h, "minutes": m}
        })

    return plan

# --------- Routes ---------
@app.get("/")
def home():
    """
    Simple GET route to check server status
    """
    return {"message": "FocusFox API is running!"}

@app.post("/focusfox")
def focusfox(data: InputData):
    print("Received JSON:", data.dict())
    mood = (data.mood or "neutral").lower()
    plan = tiny_reorder(data.tasks, mood, data.time_available)
    motivation = MOTIVATIONS.get(mood, MOTIVATIONS["neutral"])

    return {
        "greeting": f"Here’s a tiny plan for when you’re {mood}:",
        "plan": plan,
        "motivation": motivation
    }
