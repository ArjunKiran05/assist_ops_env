from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import AssistOpsAction, AssistOpsObservation, Helper, Request


class AssistOpsEnvClient(EnvClient[AssistOpsAction, AssistOpsObservation, State]):
    """Client for the Assist Ops environment."""

    def _step_payload(self, action: AssistOpsAction) -> Dict:
        payload = {"action_type": action.action_type}
        if action.helper_id is not None:
            payload["helper_id"] = action.helper_id
        if action.request_id is not None:
            payload["request_id"] = action.request_id
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[AssistOpsObservation]:
        obs_data = payload.get("observation", {})
        observation = AssistOpsObservation(
            time_step=obs_data.get("time_step", 0),
            requests=[Request(**item) for item in obs_data.get("requests", [])],
            helpers=[Helper(**item) for item in obs_data.get("helpers", [])],
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
