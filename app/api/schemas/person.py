from pydantic import BaseModel


class Person(BaseModel):
    id: str
    name: str
    company: str | None = None
    designation: str | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    email: str | None = None
    alternate_email: str | None = None
    website: str | None = None
