from datetime import datetime
from pydantic import BaseModel, Field

class AgentConfigCreate(BaseModel):
    name: str = Field(..., max_length=200)
    agent_type: str = Field(..., pattern="^(langgraph|openai_compatible|http|python_fn)$")
    config: dict = Field(default_factory=dict)
    description: str = ""

class AgentConfigUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    agent_type: str | None = Field(default=None, pattern="^(langgraph|openai_compatible|http|python_fn)$")
    config: dict | None = None
    description: str | None = None

class AgentConfigResponse(BaseModel):
    id: int
    name: str
    agent_type: str
    config: dict
    description: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
