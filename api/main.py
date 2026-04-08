from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graders import GRADERS as TASK_GRADERS
from env.environment import AssistOpsEnv
from env.models import Action, Observation
from env.grader import compute_score
from fastapi.responses import RedirectResponse
from tasks import TASKS, TASKS_BY_ID

app = FastAPI()

# Global environment instance
env = AssistOpsEnv()


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
    if task_name not in TASKS_BY_ID:
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
                "id": task_data["id"],
                "name": task_data["name"],
                "difficulty": task_data["difficulty"],
                "description": task_data["description"],
                "max_steps": task_data["max_steps"],
                "reset_params": task_data["reset_params"],
                "grader": task_id in TASK_GRADERS,
                "grader_endpoint": f"/grade/{task_id}",
            }
            for task_data in TASKS
            for task_id in [task_data["id"]]
        ]
    }


# -----------------------------
# 5. Grader Endpoint
# -----------------------------
@app.get("/grade/{task_id}")
@app.post("/grade/{task_id}")
def grade_task(task_id: str):
    if task_id not in TASKS_BY_ID or task_id not in TASK_GRADERS:
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
    if task is not None and task not in TASKS_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown task")

    score = compute_score(env)
    return {"task": task or getattr(env, "current_task", None), "score": score}


@app.get("/validate")
def validate():
    task_ids = [task["id"] for task in TASKS]
    tasks_with_graders = [task_id for task_id in task_ids if task_id in TASK_GRADERS]
    return {
        "valid": len(tasks_with_graders) >= 3,
        "task_count": len(task_ids),
        "graders_count": len(TASK_GRADERS),
        "tasks_with_graders": tasks_with_graders,
        "checks": {
            "min_3_tasks": len(task_ids) >= 3,
            "all_tasks_have_graders": all(task_id in TASK_GRADERS for task_id in task_ids),
        },
    }
