import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata, State

try:
    from ..models import AssistOpsAction, AssistOpsObservation, Helper, Request
except (ModuleNotFoundError, ImportError):
    from models import AssistOpsAction, AssistOpsObservation, Helper, Request


class AssistOpsEnvEnvironment(Environment):
    """Assist Ops emergency-response environment in the official OpenEnv shape."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, seed: int = 42):
        super().__init__()
        self.seed = seed
        self._rng = random.Random(seed)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.time_step = 0
        self.current_task = "easy"
        self.requests: list[Request] = []
        self.helpers: list[Helper] = []
        self.total_requests = 0
        self.resolved_requests = 0
        self.total_wait_time = 0
        self.used_trust_scores: list[float] = []

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task: str = "easy",
        **kwargs,
    ) -> AssistOpsObservation:
        if seed is not None:
            self.seed = seed
        self._rng = random.Random(self.seed)
        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )
        self.time_step = 0
        self.current_task = task

        if task == "easy":
            self.requests = [
                Request(id="R1", type="medical", severity=2),
                Request(id="R2", type="delivery", severity=1),
            ]
            self.helpers = [
                Helper(id="H1", skills=["medical"], trust_score=0.9),
                Helper(id="H2", skills=["delivery"], trust_score=0.9),
            ]
        elif task == "medium":
            self.requests = [
                Request(id="R1", type="medical", severity=3),
                Request(id="R2", type="medical", severity=1),
                Request(id="R3", type="delivery", severity=2),
            ]
            self.helpers = [
                Helper(id="H1", skills=["medical"], trust_score=0.8),
                Helper(id="H2", skills=["delivery"], trust_score=0.7),
            ]
        elif task == "hard":
            self.requests = [
                Request(id="R1", type="medical", severity=3),
                Request(id="R2", type="delivery", severity=2),
                Request(id="R3", type="medical", severity=1),
                Request(id="R4", type="delivery", severity=3),
            ]
            self.helpers = [
                Helper(id="H1", skills=["medical"], trust_score=0.9),
                Helper(id="H2", skills=["delivery"], trust_score=0.6),
            ]
        else:
            raise ValueError("Invalid task type")

        self.total_requests = len(self.requests)
        self.resolved_requests = 0
        self.total_wait_time = 0
        self.used_trust_scores = []

        return self._observation(done=False, reward=0.0)

    def step(
        self,
        action: AssistOpsAction,
        timeout_s: float | None = None,
        **kwargs,
    ) -> AssistOpsObservation:
        reward = 0.0
        done = False

        if self.requests and all(request.resolved for request in self.requests):
            return self._observation(done=True, reward=0.0)

        if action.action_type == "assign":
            helper = next((item for item in self.helpers if item.id == action.helper_id), None)
            request = next((item for item in self.requests if item.id == action.request_id), None)

            if helper and request and not helper.busy and not request.assigned:
                if request.type in helper.skills:
                    reward += 1.0
                else:
                    reward -= 1.0

                helper.busy = True
                helper.current_request = request.id
                helper.time_to_complete = request.severity + 1
                request.assigned = True
                self.used_trust_scores.append(helper.trust_score)
            else:
                reward -= 0.5

        self.time_step += 1
        self._state.step_count += 1

        if self.current_task == "hard" and self.time_step % 2 == 0:
            new_request = Request(
                id=f"R{self.total_requests + 1}",
                type=self._rng.choice(["medical", "delivery"]),
                severity=self._rng.randint(1, 3),
            )
            self.requests.append(new_request)
            self.total_requests += 1

        for request in self.requests:
            if not request.assigned and not request.resolved:
                request.waiting_time += 1
                self.total_wait_time += 1

        for helper in self.helpers:
            if helper.busy:
                helper.time_to_complete -= 1
                if helper.time_to_complete <= 0:
                    request = next(
                        (item for item in self.requests if item.id == helper.current_request),
                        None,
                    )
                    if request:
                        request.resolved = True
                        self.resolved_requests += 1
                        reward += 1.0 + (0.5 * request.severity)
                    helper.busy = False
                    helper.current_request = None

        for request in self.requests:
            if not request.resolved and not request.assigned:
                reward -= 0.1 * request.severity

        if all(request.resolved for request in self.requests):
            done = True
        if self.time_step >= 10:
            done = True

        return self._observation(done=done, reward=reward)

    @property
    def state(self) -> State:
        return self._state

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="assist_ops_env",
            description="Assist Ops environment for community emergency assistance",
            version="1.0.0",
        )

    def _observation(self, done: bool, reward: float | None) -> AssistOpsObservation:
        return AssistOpsObservation(
            time_step=self.time_step,
            requests=self.requests,
            helpers=self.helpers,
            done=done,
            reward=reward,
            metadata={"task": self.current_task},
        )
