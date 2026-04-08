from __future__ import annotations

from typing import Any


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _float_metric(run_output: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = run_output.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_metric(run_output: dict[str, Any], key: str, default: int = 0) -> int:
    value = run_output.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _wait_score(avg_wait_time: float, baseline: float) -> float:
    if baseline <= 0:
        return 1.0
    return _clamp(1.0 - (avg_wait_time / baseline))


def _validity_score(invalid_actions: int, baseline: int) -> float:
    if baseline <= 0:
        return 1.0
    return _clamp(1.0 - (invalid_actions / baseline))


def _metrics(run_output: dict[str, Any]) -> dict[str, float]:
    resolved_ratio = _clamp(_float_metric(run_output, "resolved_ratio"))
    priority_coverage = _clamp(
        _float_metric(run_output, "priority_coverage", resolved_ratio)
    )
    skill_match_ratio = _clamp(
        _float_metric(run_output, "skill_match_ratio", resolved_ratio)
    )
    avg_wait_time = max(0.0, _float_metric(run_output, "avg_wait_time"))
    avg_trust = _clamp(_float_metric(run_output, "avg_trust"))
    invalid_actions = max(0, _int_metric(run_output, "invalid_actions"))

    return {
        "resolved_ratio": resolved_ratio,
        "priority_coverage": priority_coverage,
        "skill_match_ratio": skill_match_ratio,
        "avg_wait_time": avg_wait_time,
        "avg_trust": avg_trust,
        "invalid_actions": float(invalid_actions),
        "wait_score_easy": _wait_score(avg_wait_time, baseline=3.0),
        "wait_score_medium": _wait_score(avg_wait_time, baseline=4.0),
        "wait_score_hard": _wait_score(avg_wait_time, baseline=5.0),
        "validity_score": _validity_score(invalid_actions, baseline=3),
    }


def grade_easy(run_output: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics(run_output)
    score = (
        (0.60 * metrics["resolved_ratio"])
        + (0.25 * metrics["skill_match_ratio"])
        + (0.15 * metrics["wait_score_easy"])
    )
    return {
        "score": round(_clamp(score), 4),
        "details": {
            "resolved_ratio": metrics["resolved_ratio"],
            "skill_match_ratio": metrics["skill_match_ratio"],
            "wait_score": metrics["wait_score_easy"],
        },
    }


def grade_medium(run_output: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics(run_output)
    score = (
        (0.45 * metrics["resolved_ratio"])
        + (0.25 * metrics["priority_coverage"])
        + (0.15 * metrics["wait_score_medium"])
        + (0.15 * metrics["validity_score"])
    )
    return {
        "score": round(_clamp(score), 4),
        "details": {
            "resolved_ratio": metrics["resolved_ratio"],
            "priority_coverage": metrics["priority_coverage"],
            "wait_score": metrics["wait_score_medium"],
            "validity_score": metrics["validity_score"],
        },
    }


def grade_hard(run_output: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics(run_output)
    score = (
        (0.35 * metrics["resolved_ratio"])
        + (0.25 * metrics["priority_coverage"])
        + (0.15 * metrics["wait_score_hard"])
        + (0.15 * metrics["avg_trust"])
        + (0.10 * metrics["validity_score"])
    )
    return {
        "score": round(_clamp(score), 4),
        "details": {
            "resolved_ratio": metrics["resolved_ratio"],
            "priority_coverage": metrics["priority_coverage"],
            "wait_score": metrics["wait_score_hard"],
            "avg_trust": metrics["avg_trust"],
            "validity_score": metrics["validity_score"],
        },
    }


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

GRADER_METADATA = {
    "easy": {
        "grader": "grade_easy",
        "score_range": [0.0, 1.0],
        "rubric": "Scores direct skill matching, full resolution, and low wait time.",
        "required_run_output": [
            "resolved_ratio",
            "skill_match_ratio",
            "avg_wait_time",
        ],
    },
    "medium": {
        "grader": "grade_medium",
        "score_range": [0.0, 1.0],
        "rubric": "Scores prioritized resolution, trajectory quality, and low invalid actions.",
        "required_run_output": [
            "resolved_ratio",
            "priority_coverage",
            "avg_wait_time",
            "invalid_actions",
        ],
    },
    "hard": {
        "grader": "grade_hard",
        "score_range": [0.0, 1.0],
        "rubric": "Scores sustained high-priority coverage, trusted dispatch, and efficient control.",
        "required_run_output": [
            "resolved_ratio",
            "priority_coverage",
            "avg_wait_time",
            "avg_trust",
            "invalid_actions",
        ],
    },
}


def grade(task_id: str, run_output: dict[str, Any]) -> dict[str, Any]:
    grader = GRADERS.get(task_id)
    if grader is None:
        raise ValueError(f"Unknown task_id: {task_id}")
    return grader(run_output)
