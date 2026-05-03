from dataclasses import dataclass
from datetime import datetime

from app.schemas import GeneratedQAOutput, GenerateRequest


@dataclass(frozen=True)
class GenerationRecord:
    id: int
    title: str
    generated_at: datetime
    request: GenerateRequest
    output: GeneratedQAOutput

