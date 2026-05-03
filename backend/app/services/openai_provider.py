import json
import os

from app.schemas import GeneratedQAOutput, GenerateRequest, ModelMetadata, RetrievedContext
from app.services.llm_provider import LLMProvider, LLMProviderError, load_prompt
from app.services.mock_llm_provider import MockLLMProvider


class OpenAIProvider(LLMProvider):
    """Optional provider used only when OPENAI_API_KEY and AI_PROVIDER=openai are set."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMProviderError("OPENAI_API_KEY is required for the OpenAI provider")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMProviderError("Install the openai package to use the OpenAI provider") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.prompt_version = os.getenv("PROMPT_VERSION", "qa_generation_v1")

    def generate(
        self,
        request: GenerateRequest,
        retrieved_context: list[RetrievedContext] | None = None,
    ) -> GeneratedQAOutput:
        context = retrieved_context or []
        qa_prompt = load_prompt(f"{self.prompt_version}.txt")
        bug_prompt = load_prompt("bug_report_v1.txt")
        payload = {
            "input": request.model_dump(mode="json"),
            "retrieved_context": [item.model_dump(mode="json") for item in context],
            "required_prompt_version": self.prompt_version,
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "\n\n".join([qa_prompt, bug_prompt]),
                    },
                    {"role": "user", "content": json.dumps(payload)},
                ],
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMProviderError("OpenAI returned an empty response")
            output = GeneratedQAOutput.model_validate(json.loads(content))
            output.retrieved_context = context
            output.model_metadata = ModelMetadata(
                provider="openai",
                prompt_version=self.prompt_version,
                used_rag=bool(context),
                retrieved_context_count=len(context),
            )
            return output
        except Exception:
            # Keep the app usable during malformed model responses or transient API failures.
            return MockLLMProvider().generate(request, retrieved_context=context)
