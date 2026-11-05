from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./agentbench.db"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1"
    llm_judge_model: str = "gpt-4.1"
    model_config = {"env_prefix": "AGENTBENCH_", "env_file": ".env"}


settings = Settings()
