try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

from fastapi import HTTPException
from pydantic import BaseModel

try:
    from ..models import AssistOpsAction, AssistOpsObservation
    from .assist_ops_env_environment import AssistOpsEnvEnvironment
except (ModuleNotFoundError, ImportError):
    from models import AssistOpsAction, AssistOpsObservation
    from server.assist_ops_env_environment import AssistOpsEnvEnvironment

from grader import GRADERS
from tasks import TASKS, TASKS_BY_ID


app = create_app(
    AssistOpsEnvEnvironment,
    AssistOpsAction,
    AssistOpsObservation,
    env_name="assist_ops_env",
    max_concurrent_envs=1,
)


class GradePayload(BaseModel):
    task_id: str
    run_output: dict = {}


@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                **task,
                "grader": True,
                "grader_endpoint": f"/grade/{task['id']}",
            }
            for task in TASKS
        ]
    }


@app.get("/grade/{task_id}")
@app.post("/grade/{task_id}")
def grade_task(task_id: str):
    if task_id not in TASKS_BY_ID or task_id not in GRADERS:
        raise HTTPException(status_code=404, detail="Unknown task")
    return {"task_id": task_id, "grader": GRADERS[task_id].__name__, "score": 0.0}


@app.post("/grader")
def grader(payload: GradePayload):
    if payload.task_id not in TASKS_BY_ID or payload.task_id not in GRADERS:
        raise HTTPException(status_code=404, detail="Unknown task")
    return {"task_id": payload.task_id, **GRADERS[payload.task_id](payload.run_output)}


@app.get("/grader")
def grader_query(task: str):
    if task not in TASKS_BY_ID or task not in GRADERS:
        raise HTTPException(status_code=404, detail="Unknown task")
    return {"task": task, "score": 0.0}


@app.get("/validate")
def validate():
    task_ids = [task["id"] for task in TASKS]
    tasks_with_graders = [task_id for task_id in task_ids if task_id in GRADERS]
    return {
        "valid": len(tasks_with_graders) >= 3,
        "task_count": len(task_ids),
        "graders_count": len(GRADERS),
        "tasks_with_graders": tasks_with_graders,
    }


def main(host: str = "0.0.0.0", port: int = 7860):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    if args.port == 7860:
        main()
    else:
        main(port=args.port)
