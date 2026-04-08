from typing import Optional

from fastapi import FastAPI, HTTPException
from env.environment import AssistOpsEnv
from env.models import Action
from env.grader import compute_score
from fastapi.responses import RedirectResponse

app = FastAPI()

# Global environment instance
env = AssistOpsEnv()
TASKS = {
    "easy": "Basic matching with equal helpers",
    "medium": "Limited helpers, prioritization required",
    "hard": "Dynamic requests with time pressure",
}


# -----------------------------
# Root Route
# -----------------------------
@app.get("/")
def home():
    return RedirectResponse(url="/docs")


# -----------------------------
# 1. Reset Endpoint
# -----------------------------
@app.post("/reset")
def reset(task: str = "easy"):
    obs = env.reset(task)
    return obs


# -----------------------------
# 2. Step Endpoint
# -----------------------------
@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info
    }


# -----------------------------
# 3. State Endpoint
# -----------------------------
@app.get("/state")
def state():
    return env._get_observation()


# -----------------------------
# 4. Tasks Endpoint
# -----------------------------
@app.get("/tasks")
def tasks():
    return [
        {
            "name": task_name,
            "description": description,
            "grader": f"/grader?task={task_name}",
        }
        for task_name, description in TASKS.items()
    ]


# -----------------------------
# 5. Grader Endpoint
# -----------------------------
@app.get("/grader")
@app.post("/grader")
def grader(task: Optional[str] = None):
    if task is not None and task not in TASKS:
        raise HTTPException(status_code=404, detail="Unknown task")

    score = compute_score(env)
    return {"task": task or getattr(env, "current_task", None), "score": score}
