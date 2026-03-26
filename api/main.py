from fastapi import FastAPI
from env.environment import AssistOpsEnv
from env.models import Action
from env.grader import compute_score

app = FastAPI()

# Global environment instance
env = AssistOpsEnv()


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
    return {
        "tasks": ["easy", "medium", "hard"],
        "description": {
            "easy": "Basic matching with equal helpers",
            "medium": "Limited helpers, prioritization required",
            "hard": "Dynamic requests with time pressure"
        }
    }


# -----------------------------
# 5. Grader Endpoint
# -----------------------------
@app.get("/grader")
def grader():
    score = compute_score(env)
    return {"score": score}