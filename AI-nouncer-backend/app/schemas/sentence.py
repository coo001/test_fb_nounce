from pydantic import BaseModel


class Sentence(BaseModel):
    id: str
    text: str
    length_tier: str = "short"  # "short" | "long" | "paragraph"
    target_patterns: list[str] = []
