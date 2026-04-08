from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from grader import GRADERS as TASK_GRADERS
from env.environment import AssistOpsEnv
from env.models import Action, Observation
from env.grader import compute_score
from fastapi.responses import RedirectResponse

app = FastAPI()

# Global environment instance
env = AssistOpsEnv()
TASKS = {
    "easy": {
        "name": "Basic Emergency Matching",
        "difficulty": "easy",
        "description": "Match one helper to one request with direct skill alignment.",
    },
    "medium": {
        "name": "Prioritized Limited-Helper Dispatch",
        "difficulty": "medium",
        "description": "Allocate scarce helpers across mixed-priority requests.",
    },
    "hard": {
        "name": "Dynamic Community Assistance",
        "difficulty": "hard",
        "description": "Handle dynamic incoming requests under sustained time pressure.",
    },
}


class ResetPayload(BaseModel):
    task: str = "easy"
    seed: Optional[int] = None
    episode_id: Optional[str] = None


class ResetResponse(BaseModel):
    observation: Observation
    reward: Optional[float] = None
    done: bool = False


class StepPayload(BaseModel):
    action: Action
    timeout_s: Optional[float] = None
    request_id: Optional[str] = None


class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict[str, Any] = {}


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
def reset(payload: Optional[ResetPayload] = None, task: Optional[str] = None):
    task_name = task or (payload.task if payload else "easy")
    if task_name not in TASKS:
        raise HTTPException(status_code=404, detail="Unknown task")

    obs = env.reset(task_name)
    return ResetResponse(observation=obs)


# -----------------------------
# 2. Step Endpoint
# -----------------------------
@app.post("/step")
def step(payload: dict[str, Any]):
    if "action" in payload:
        action = StepPayload(**payload).action
    else:
        action = Action(**payload)

    obs, reward, done, info = env.step(action)
    return StepResponse(
        observation=obs,
        reward=reward,
        done=done,
        info=info,
    )


# -----------------------------
# 3. State Endpoint
# -----------------------------
@app.get("/state")
def state():
    return env._get_observation()


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metadata")
def metadata():
    return {
        "name": "assist_ops_env",
        "description": "Assist Ops environment for community emergency assistance",
    }


@app.get("/schema")
def schema():
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": Observation.model_json_schema(),
    }


@app.post("/mcp")
def mcp():
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32600, "message": "Invalid Request"},
    }


# -----------------------------
# 4. Tasks Endpoint
# -----------------------------
@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                "id": task_id,
                "name": task_data["name"],
                "difficulty": task_data["difficulty"],
                "description": task_data["description"],
                "grader": task_id in TASK_GRADERS,
                "grader_endpoint": f"/grade/{task_id}",
            }
            for task_id, task_data in TASKS.items()
        ]
    }


# -----------------------------
# 5. Grader Endpoint
# -----------------------------
@app.get("/grade/{task_id}")
@app.post("/grade/{task_id}")
def grade_task(task_id: str):
    if task_id not in TASKS or task_id not in TASK_GRADERS:
        raise HTTPException(status_code=404, detail="Unknown task")

    score = compute_score(env)
    return {
        "task_id": task_id,
        "grader": TASK_GRADERS[task_id].__name__,
        "score": score,
    }


@app.get("/grader")
@app.post("/grader")
def grader(task: Optional[str] = None):
    if task is not None and task not in TASKS:
        raise HTTPException(status_code=404, detail="Unknown task")

    score = compute_score(env)
    return {"task": task or getattr(env, "current_task", None), "score": score}


@app.get("/validate")
def validate():
    tasks_with_graders = [task_id for task_id in TASKS if task_id in TASK_GRADERS]
    return {
        "valid": len(tasks_with_graders) >= 3,
        "task_count": len(TASKS),
        "graders_count": len(TASK_GRADERS),
        "tasks_with_graders": tasks_with_graders,
    }
