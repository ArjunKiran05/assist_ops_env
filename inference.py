import asyncio
import os
from openai import OpenAI
from typing import List, Optional

from env.environment import AssistOpsEnv
from env.models import Action


TASK_NAME = "easy"
BENCHMARK = "assist_ops"
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
MAX_STEPS = 10


def log_start(task: str, env: str, model: str):
    print(
        f"[START] task={task} env={env} model={model}",
        flush=True
    )


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error if error else 'null'}",
        flush=True
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True
    )


def choose_action(obs, client):
    prompt = f"""
Requests:
{[(r.id, r.type, r.severity, r.assigned, r.resolved) for r in obs.requests]}

Helpers:
{[(h.id, h.skills, h.busy) for h in obs.helpers]}

Choose the best assignment.
Respond ONLY in this format:
HELPER_ID,REQUEST_ID
Example:
H1,R1
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that assigns the best helper to the highest priority unresolved request."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        text = response.choices[0].message.content.strip()
        helper_id, request_id = [x.strip() for x in text.split(",")]

        return Action(
            action_type="assign",
            helper_id=helper_id,
            request_id=request_id
        )

    except Exception:
        # fallback if model fails
        for req in obs.requests:
            if not req.assigned and not req.resolved:
                for helper in obs.helpers:
                    if not helper.busy and req.type in helper.skills:
                        return Action(
                            action_type="assign",
                            helper_id=helper.id,
                            request_id=req.id
                        )

        return Action(
            action_type="assign",
            helper_id="H1",
            request_id="R1"
        )


async def main():
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN
    )
    env = AssistOpsEnv(seed=42)

    rewards = []
    steps_taken = 0
    success = False
    total_reward = 0.0

    log_start(TASK_NAME, BENCHMARK, MODEL_NAME)

    try:
        obs = env.reset(task=TASK_NAME)

        for step in range(1, MAX_STEPS + 1):
            action = choose_action(obs, client)

            obs, reward, done, info = env.step(action)

            rewards.append(reward)
            total_reward += reward
            steps_taken = step

            action_str = (
                f"assign(helper={action.helper_id},request={action.request_id})"
            )

            log_step(
                step=step,
                action=action_str,
                reward=reward,
                done=done,
                error=None
            )

            if done:
                break

        score = max(0.0, min(total_reward / 10.0, 1.0))
        success = score > 0.3

    except Exception as e:
        print(f"[DEBUG] {str(e)}", flush=True)

    finally:
        log_end(
            success=success,
            steps=steps_taken,
            score=score if 'score' in locals() else 0.0,
            rewards=rewards
        )


if __name__ == "__main__":
    asyncio.run(main())