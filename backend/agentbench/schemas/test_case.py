from datetime import datetime
from pydantic import BaseModel, Field

class TestCaseCreate(BaseModel):
    title: str = Field(..., max_length=200)
    input_text: str
    expected_behavior: str
    scoring_criteria: str = ""
    tags: list[str] = Field(default_factory=list)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    category: str = Field(default="")

class TestCaseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    input_text: str | None = None
    expected_behavior: str | None = None
    scoring_criteria: str | None = None
    tags: list[str] | None = None
    difficulty: str | None = Field(default=None, pattern="^(easy|medium|hard)$")
    category: str | None = None

class TestCaseResponse(BaseModel):
    id: int
    title: str
    input_text: str
    expected_behavior: str
    scoring_criteria: str
    tags: list[str]
    difficulty: str
    category: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
