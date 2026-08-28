import os
from dataclasses import dataclass

from app.core.environment import load_project_environment


load_project_environment()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "People Search")
    app_env: str = os.getenv("APP_ENV", "local")
    sample_people_path: str = os.getenv("SAMPLE_PEOPLE_PATH", "data/sample/people.json")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://people_search:people_search@localhost:5432/people_search")
    search_provider: str = os.getenv("SEARCH_PROVIDER", "mock").lower()


settings = Settings()
