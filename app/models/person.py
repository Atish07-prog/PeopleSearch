from dataclasses import dataclass, field


@dataclass(frozen=True)
class PersonRecord:
    id: str
    full_name: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    email: str | None = None
    profile_url: str | None = None
    skills: list[str] = field(default_factory=list)
    source: str = "mock"
