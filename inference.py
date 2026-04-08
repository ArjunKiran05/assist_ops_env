import asyncio
import os
import re
import socket
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional
from urllib.error import URLError
from urllib.request import urlopen

from openai import OpenAI

from client import AssistOpsEnvClient
from grader import grade
from models import AssistOpsAction, AssistOpsObservation


TASK_NAMES = ("easy", "medium", "hard")
BENCHMARK = "assist_ops"
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
MAX_STEPS = 10
ROOT_DIR = Path(__file__).resolve().parent


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error if error else 'null'}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _wait_for_server(base_url: str, process: subprocess.Popen[str], timeout_s: float = 20.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(output or "Environment server exited before becoming ready.")
        try:
            with urlopen(f"{base_url}/health", timeout=1.0) as response:
                if response.status == 200:
                    return
        except URLError:
            time.sleep(0.2)
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for environment server at {base_url}.")


@asynccontextmanager
async def _local_env_server():
    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [sys.executable, "-m", "server.app", "--port", str(port)],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_server(base_url, process)
        yield base_url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _heuristic_action(observation: AssistOpsObservation) -> AssistOpsAction:
    open_requests = sorted(
        [request for request in observation.requests if not request.assigned and not request.resolved],
        key=lambda request: (-request.severity, request.waiting_time, request.id),
    )
    for request in open_requests:
        matching_helper = next(
            (
                helper
                for helper in observation.helpers
                if not helper.busy and request.type in helper.skills
            ),
            None,
        )
        if matching_helper is not None:
            return AssistOpsAction(
                action_type="assign",
                helper_id=matching_helper.id,
                request_id=request.id,
            )
    return AssistOpsAction(action_type="wait")


def _choose_action(observation: AssistOpsObservation, client: Optional[OpenAI]) -> AssistOpsAction:
    if client is None:
        return _heuristic_action(observation)

    prompt = f"""
Requests:
{[(request.id, request.type, request.severity, request.assigned, request.resolved) for request in observation.requests]}

Helpers:
{[(helper.id, helper.skills, helper.busy) for helper in observation.helpers]}

Pick the best helper/request assignment.
Respond with ONLY:
HELPER_ID,REQUEST_ID
or
WAIT
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You assign community helpers to open assistance requests. "
                        "Prefer unresolved high-severity requests, valid skill matches, and idle helpers."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            if line.upper() == "WAIT":
                return AssistOpsAction(action_type="wait")

            match = re.fullmatch(r"([A-Za-z0-9_-]+)\s*,\s*([A-Za-z0-9_-]+)", line)
            if match:
                helper_id, request_id = match.groups()
                return AssistOpsAction(
                    action_type="assign",
                    helper_id=helper_id,
                    request_id=request_id,
                )

        compact = " ".join(lines)
        match = re.search(r"([A-Za-z0-9_-]+)\s*,\s*([A-Za-z0-9_-]+)", compact)
        if match:
            helper_id, request_id = match.groups()
            return AssistOpsAction(
                action_type="assign",
                helper_id=helper_id,
                request_id=request_id,
            )

        if "WAIT" in text.upper():
            return AssistOpsAction(action_type="wait")

        raise ValueError(f"Could not parse model action: {text!r}")
    except Exception:
        return _heuristic_action(observation)


def _action_string(action: AssistOpsAction) -> str:
    if action.action_type == "wait":
        return "wait()"
    return f"assign(helper={action.helper_id},request={action.request_id})"


def _summarize_run(
    observation: AssistOpsObservation,
    assigned_trust_scores: List[float],
    skill_matches: int,
    assignment_attempts: int,
    invalid_actions: int,
) -> dict:
    total_requests = len(observation.requests)
    resolved_requests = sum(1 for request in observation.requests if request.resolved)
    total_severity = sum(request.severity for request in observation.requests) or 1
    resolved_severity = sum(
        request.severity for request in observation.requests if request.resolved
    )
    avg_wait_time = (
        sum(request.waiting_time for request in observation.requests) / total_requests
        if total_requests
        else 0.0
    )
    avg_trust = (
        sum(assigned_trust_scores) / len(assigned_trust_scores)
        if assigned_trust_scores
        else 0.0
    )
    return {
        "success": resolved_requests == total_requests and total_requests > 0,
        "resolved_ratio": resolved_requests / total_requests if total_requests else 0.0,
        "priority_coverage": resolved_severity / total_severity,
        "skill_match_ratio": (
            skill_matches / assignment_attempts if assignment_attempts else 0.0
        ),
        "avg_wait_time": avg_wait_time,
        "avg_trust": avg_trust,
        "invalid_actions": invalid_actions,
    }


async def _run_task(task_name: str, llm_client: Optional[OpenAI], base_url: str) -> float:
    rewards: List[float] = []
    assigned_trust_scores: List[float] = []
    assignment_attempts = 0
    skill_matches = 0
    invalid_actions = 0
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    async with AssistOpsEnvClient(base_url=base_url) as env:
        result = await env.reset(task=task_name)

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            observation = result.observation
            action = _choose_action(observation, llm_client)

            if action.action_type == "assign":
                helper = next(
                    (item for item in observation.helpers if item.id == action.helper_id),
                    None,
                )
                request = next(
                    (item for item in observation.requests if item.id == action.request_id),
                    None,
                )
                if (
                    helper is None
                    or request is None
                    or helper.busy
                    or request.assigned
                    or request.resolved
                ):
                    invalid_actions += 1
                else:
                    assignment_attempts += 1
                    if request.type in helper.skills:
                        skill_matches += 1
                    assigned_trust_scores.append(helper.trust_score)

            result = await env.step(action)

            reward = result.reward or 0.0
            done = result.done
            rewards.append(reward)
            steps_taken = step

            log_step(
                step=step,
                action=_action_string(action),
                reward=reward,
                done=done,
                error=None,
            )

            if done:
                break

        run_output = _summarize_run(
            observation=result.observation,
            assigned_trust_scores=assigned_trust_scores,
            skill_matches=skill_matches,
            assignment_attempts=assignment_attempts,
            invalid_actions=invalid_actions,
        )
        score = float(grade(task_name, run_output)["score"])
        success = score >= 0.5

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return score


async def main() -> None:
    llm_client = None
    if API_KEY:
        llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    task_override = os.getenv("TASK_NAME")
    task_names = (task_override,) if task_override else TASK_NAMES

    async with _local_env_server() as base_url:
        for task_name in task_names:
            await _run_task(task_name=task_name, llm_client=llm_client, base_url=base_url)


if __name__ == "__main__":
    asyncio.run(main())
