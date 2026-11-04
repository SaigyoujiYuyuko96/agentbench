from pydantic import BaseModel

class RunStepResponse(BaseModel):
    id: int
    test_run_id: int
    sequence: int
    step_type: str
    name: str
    input_json: dict
    output_json: dict
    latency_ms: int
    token_usage_input: int
    token_usage_output: int
    status: str
    error_message: str | None
    model_config = {"from_attributes": True}
