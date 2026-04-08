from typing import List, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field


class Request(BaseModel):
    id: str = Field(..., description="Request identifier")
    type: str = Field(..., description="Request category")
    severity: int = Field(..., description="Priority severity from 1 to 3")
    waiting_time: int = Field(default=0, description="Unassigned wait time")
    assigned: bool = Field(default=False, description="Whether a helper is assigned")
    resolved: bool = Field(default=False, description="Whether the request is resolved")


class Helper(BaseModel):
    id: str = Field(..., description="Helper identifier")
    skills: List[str] = Field(..., description="Skills supported by this helper")
    trust_score: float = Field(..., description="Trust score for the helper")
    busy: bool = Field(default=False, description="Whether the helper is busy")
    current_request: Optional[str] = Field(
        default=None, description="Assigned request id if busy"
    )
    time_to_complete: int = Field(default=0, description="Remaining work steps")


class AssistOpsAction(Action):
    action_type: str = Field(..., description="assign or wait")
    helper_id: Optional[str] = Field(default=None, description="Helper id to assign")
    request_id: Optional[str] = Field(default=None, description="Request id to assign")


class AssistOpsObservation(Observation):
    time_step: int = Field(default=0, description="Current time step")
    requests: List[Request] = Field(default_factory=list, description="Open requests")
    helpers: List[Helper] = Field(default_factory=list, description="Available helpers")
