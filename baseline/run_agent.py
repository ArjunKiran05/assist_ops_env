import requests

BASE_URL = "http://127.0.0.1:8000"


def run_episode(task="easy"):
    # Reset environment
    response = requests.post(f"{BASE_URL}/reset", params={"task": task})
    obs = response.json()

    done = False

    while not done:
        # Simple baseline strategy:
        # assign first free helper to first unassigned request

        helpers = obs["helpers"]
        requests_list = obs["requests"]

        action = {
            "action_type": "wait"
        }

        for h in helpers:
            if not h["busy"]:
                for r in requests_list:
                    if not r["assigned"]:
                        action = {
                            "action_type": "assign",
                            "helper_id": h["id"],
                            "request_id": r["id"]
                        }
                        break
                break

        # Send step request
        response = requests.post(f"{BASE_URL}/step", json=action)
        data = response.json()

        obs = data["observation"]
        done = data["done"]

    # Get final score
    score = requests.get(f"{BASE_URL}/grader").json()["score"]

    return score


if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        score = run_episode(task)
        print(f"{task.upper()} SCORE: {score:.2f}")