from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas import GeneratedQAOutput, GenerateRequest, RetrievedContext


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        request: GenerateRequest,
        retrieved_context: list[RetrievedContext] | None = None,
    ) -> GeneratedQAOutput:
        """Generate structured QA output for a requirement."""


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot return valid QA output."""


def load_prompt(prompt_name: str) -> str:
    prompt_path = PROMPT_DIR / prompt_name
    if not prompt_path.exists():
        raise LLMProviderError(f"Prompt template not found: {prompt_name}")
    return prompt_path.read_text(encoding="utf-8")
