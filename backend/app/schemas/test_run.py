from datetime import datetime
from pydantic import BaseModel

class TestRunResponse(BaseModel):
    id: int
    test_case_id: int
    agent_config_id: int
    status: str
    agent_output: str
    duration_ms: int
    total_tokens: int
    cost_estimate: float
    error_message: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
