import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "People Search")
    app_env: str = os.getenv("APP_ENV", "local")
    sample_people_path: str = os.getenv("SAMPLE_PEOPLE_PATH", "data/sample/people.json")


settings = Settings()
