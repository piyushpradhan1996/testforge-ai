import re
from typing import Any

from pydantic import ValidationError

from app.schemas import GeneratedQAOutput, GenerateRequest, GuardrailResult, RetrievedContext


ENDPOINT_PATTERN = re.compile(
    r"(?:(?:GET|POST|PUT|PATCH|DELETE)\s+)?(/[a-zA-Z0-9_./{}-]+)",
    re.IGNORECASE,
)
REQUIRED_SECTIONS = [
    "positive_test_cases",
    "negative_test_cases",
    "edge_cases",
    "api_test_scenarios",
    "bug_report_draft",
    "qa_checklist",
]
BUG_REPORT_FIELDS = [
    "title",
    "description",
    "steps_to_reproduce",
    "expected_result",
    "actual_result",
    "severity",
    "environment",
]


def extract_endpoints(text: str) -> set[str]:
    return {match.group(1).rstrip(".,)") for match in ENDPOINT_PATTERN.finditer(text or "")}


class GuardrailService:
    def validate(
        self,
        output: GeneratedQAOutput | dict[str, Any],
        request: GenerateRequest | None = None,
        retrieved_context: list[RetrievedContext] | None = None,
    ) -> GuardrailResult:
        warnings: list[str] = []
        errors: list[str] = []

        payload = output.model_dump(mode="json") if isinstance(output, GeneratedQAOutput) else output

        for section in REQUIRED_SECTIONS:
            if section not in payload:
                errors.append(f"Missing required section: {section}")

        if errors:
            return GuardrailResult(passed=False, warnings=warnings, errors=errors)

        try:
            validated = output if isinstance(output, GeneratedQAOutput) else GeneratedQAOutput.model_validate(payload)
        except ValidationError as exc:
            return GuardrailResult(
                passed=False,
                warnings=warnings,
                errors=[f"Generated output failed schema validation: {exc.errors()[0]['msg']}"],
            )

        if not validated.positive_test_cases:
            errors.append("Positive test cases are empty")
        if not validated.negative_test_cases:
            errors.append("Negative test cases are empty")
        if not validated.edge_cases:
            errors.append("Edge cases are empty")

        bug_payload = payload.get("bug_report_draft", {})
        for field in BUG_REPORT_FIELDS:
            if not bug_payload.get(field):
                errors.append(f"Malformed bug report draft: missing {field}")

        titles = [
            test_case.title.strip().lower()
            for test_case in [
                *validated.positive_test_cases,
                *validated.negative_test_cases,
                *validated.edge_cases,
                *validated.api_test_scenarios,
            ]
        ]
        duplicate_titles = sorted({title for title in titles if titles.count(title) > 1})
        if duplicate_titles:
            warnings.append(f"Duplicate test case titles detected: {', '.join(duplicate_titles)}")

        hallucinated = self._hallucinated_endpoints(validated, request, retrieved_context or validated.retrieved_context)
        if hallucinated:
            errors.append(f"Potential hallucinated API endpoints detected: {', '.join(sorted(hallucinated))}")

        return GuardrailResult(passed=not errors, warnings=warnings, errors=errors)

    def _hallucinated_endpoints(
        self,
        output: GeneratedQAOutput,
        request: GenerateRequest | None,
        retrieved_context: list[RetrievedContext],
    ) -> set[str]:
        allowed_text = " ".join(
            [
                request.api_notes if request else "",
                *(context.content for context in retrieved_context),
            ]
        )
        allowed = extract_endpoints(allowed_text)
        if not allowed:
            return set()

        generated_text = " ".join(
            " ".join([test_case.title, *test_case.preconditions, *test_case.steps, test_case.expected_result])
            for test_case in output.api_test_scenarios
        )
        generated = extract_endpoints(generated_text)
        return {endpoint for endpoint in generated if endpoint not in allowed}
