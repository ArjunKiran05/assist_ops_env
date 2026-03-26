from typing import List
import random

from env.models import Request, Helper, Observation,Action


class AssistOpsEnv:

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(self.seed)

        self.time_step = 0
        self.requests: List[Request] = []
        self.helpers: List[Helper] = []

        # tracking variables (for grader later)
        self.total_requests = 0
        self.resolved_requests = 0
        self.total_wait_time = 0
        self.used_trust_scores = []

    def reset(self, task: str = "easy"):
        random.seed(self.seed)
        self.time_step = 0
        self.current_task = task

        # -----------------------------
        # EASY TASK
        # -----------------------------
        if task == "easy":
            self.requests = [
                Request(id="R1", type="medical", severity=2),
                Request(id="R2", type="delivery", severity=1)
            ]

            self.helpers = [
                Helper(id="H1", skills=["medical"], trust_score=0.9),
                Helper(id="H2", skills=["delivery"], trust_score=0.9)
            ]

        # -----------------------------
        # MEDIUM TASK
        # -----------------------------
        elif task == "medium":
            self.requests = [
                Request(id="R1", type="medical", severity=3),
                Request(id="R2", type="medical", severity=1),
                Request(id="R3", type="delivery", severity=2)
            ]

            self.helpers = [
                Helper(id="H1", skills=["medical"], trust_score=0.8),
                Helper(id="H2", skills=["delivery"], trust_score=0.7)
            ]

        # -----------------------------
        # HARD TASK
        # -----------------------------
        elif task == "hard":
            self.requests = [
                Request(id="R1", type="medical", severity=3),
                Request(id="R2", type="delivery", severity=2),
                Request(id="R3", type="medical", severity=1),
                Request(id="R4", type="delivery", severity=3)
            ]

            self.helpers = [
                Helper(id="H1", skills=["medical"], trust_score=0.9),
                Helper(id="H2", skills=["delivery"], trust_score=0.6)
            ]

        else:
            raise ValueError("Invalid task type")

        # reset tracking
        self.total_requests = len(self.requests)
        self.resolved_requests = 0
        self.total_wait_time = 0
        self.used_trust_scores = []

        return self._get_observation()

    def _get_observation(self) -> Observation:
        return Observation(
            time_step=self.time_step,
            requests=self.requests,
            helpers=self.helpers
        )

    def step(self, action: Action):
        reward = 0.0
        done = False

        if self.requests and all(r.resolved for r in self.requests):
            return self._get_observation(), 0.0, True, {}

        # -----------------------------
        # 1. Apply Action
        # -----------------------------
        if action.action_type == "assign":

            helper = next((h for h in self.helpers if h.id == action.helper_id), None)
            request = next((r for r in self.requests if r.id == action.request_id), None)

            if helper and request and not helper.busy and not request.assigned:

                # Check skill match
                if request.type in helper.skills:
                    reward += 1.0
                else:
                    reward -= 1.0

                # Assign helper
                helper.busy = True
                helper.current_request = request.id
                helper.time_to_complete = request.severity + 1

                request.assigned = True

                # Track trust usage
                self.used_trust_scores.append(helper.trust_score)

            else:
                reward -= 0.5  # invalid action penalty

        # -----------------------------
        # 2. Time Progression
        # -----------------------------
        self.time_step += 1

        # -----------------------------
        # Dynamic request generation (HARD task only)
        # -----------------------------
        if hasattr(self, "current_task") and self.current_task == "hard":
            if self.time_step % 2 == 0:
                new_request = Request(
                    id=f"R{self.total_requests + 1}",
                    type=random.choice(["medical", "delivery"]),
                    severity=random.randint(1, 3)
                )
                self.requests.append(new_request)
                self.total_requests += 1

        # -----------------------------
        # Update waiting time
        # -----------------------------
        for r in self.requests:
            if not r.assigned and not r.resolved:
                r.waiting_time += 1
                self.total_wait_time += 1

        # -----------------------------
        # Update helpers (progress work)
        # -----------------------------
        for h in self.helpers:
            if h.busy:
                h.time_to_complete -= 1

                if h.time_to_complete <= 0:
                    # Complete request
                    req = next((r for r in self.requests if r.id == h.current_request), None)
                    if req:
                        req.resolved = True
                        self.resolved_requests += 1

                        # Reward for completion (with severity bonus)
                        reward += 1.0 + (0.5 * req.severity)

                    # Free helper
                    h.busy = False
                    h.current_request = None

        # -----------------------------
        # 3. Penalty for waiting (only unassigned & unresolved)
        # -----------------------------
        for r in self.requests:
            if not r.resolved and not r.assigned:
                reward -= 0.1 * r.severity

        # -----------------------------
        # 4. Check done condition
        # -----------------------------
        if all(r.resolved for r in self.requests):
            done = True

        if self.time_step >= 10:
            done = True

        # -----------------------------
        # 5. Return result
        # -----------------------------
        return self._get_observation(), reward, done, {}