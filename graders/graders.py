from typing import Any

def grade_easy(run_output: dict[str, Any]) -> dict[str, float]:
    return {"score": 1.0 if run_output.get("success", False) else 0.0}

def grade_medium(run_output: dict[str, Any]) -> dict[str, float]:
    return {"score": 1.0 if run_output.get("success", False) else 0.0}

def grade_hard(run_output: dict[str, Any]) -> dict[str, float]:
    return {"score": 1.0 if run_output.get("success", False) else 0.0}

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

def grade(task_id: str, run_output: dict[str, Any]) -> dict[str, float]:
    grader = GRADERS.get(task_id)
    if grader is None:
        raise ValueError(f"Unknown task_id: {task_id}")
    return grader(run_output)