from pydantic import BaseModel
from typing import List, Optional


class Request(BaseModel):
    id: str
    type: str
    severity: int
    waiting_time: int = 0
    assigned: bool = False
    resolved: bool = False


class Helper(BaseModel):
    id: str
    skills: List[str]
    trust_score: float
    busy: bool = False
    current_request: Optional[str] = None
    time_to_complete: int = 0


class Observation(BaseModel):
    time_step: int
    requests: List[Request]
    helpers: List[Helper]


class Action(BaseModel):
    action_type: str  # "assign" or "wait"
    helper_id: Optional[str] = None
    request_id: Optional[str] = None


class Reward(BaseModel):
    value: float