import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    db_url: str = os.getenv("DB_URL", "")
    llm_host: str = os.getenv("LLM_HOST", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")


settings = Settings()
