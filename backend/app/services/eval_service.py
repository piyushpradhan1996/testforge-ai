import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas import EvalResult, EvalRunResponse, GenerateRequest, GeneratedQAOutput
from app.services.guardrail_service import GuardrailService
from app.services.mock_llm_provider import MockLLMProvider


EVAL_DIR = Path(__file__).resolve().parents[2] / "evals"


class EvalService:
    def __init__(self) -> None:
        self.provider = MockLLMProvider()
        self.guardrails = GuardrailService()

    def run_all(self) -> EvalRunResponse:
        results = [self.run_eval(path) for path in sorted(EVAL_DIR.glob("*.json"))]
        return EvalRunResponse(provider="mock", prompt_version="qa_generation_v1", results=results)

    def run_eval(self, path: Path) -> EvalResult:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        request = GenerateRequest.model_validate(fixture["input"])
        expected_coverage = fixture.get("expected_coverage", [])

        schema_valid = True
        missing_areas: list[str] = []
        try:
            output = self.provider.generate(request, retrieved_context=[])
            GeneratedQAOutput.model_validate(output.model_dump())
        except ValidationError:
            schema_valid = False
            output = None

        if output is None:
            return EvalResult(
                name=fixture["name"],
                schema_valid=False,
                includes_positive_cases=False,
                includes_negative_cases=False,
                includes_edge_cases=False,
                includes_api_scenarios=False,
                includes_bug_report=False,
                guardrails_passed=False,
                coverage_score=0.0,
                missing_areas=expected_coverage,
            )

        guardrail_result = self.guardrails.validate(output, request=request)
        checks = {
            "positive test case": bool(output.positive_test_cases),
            "negative test case": bool(output.negative_test_cases),
            "edge case": bool(output.edge_cases),
            "api validation": bool(output.api_test_scenarios)
            and self._contains_any(output.model_dump_json(), ["validation", "schema", "4xx", "status code"]),
            "error handling": self._contains_any(
                output.model_dump_json(),
                ["error", "reject", "invalid", "malformed", "validation"],
            ),
            "bug report": bool(output.bug_report_draft.title and output.bug_report_draft.steps_to_reproduce),
        }

        for area in expected_coverage:
            if not checks.get(area, self._contains_any(output.model_dump_json(), area.split())):
                missing_areas.append(area)

        matched = len(expected_coverage) - len(missing_areas)
        coverage_score = round((matched / max(len(expected_coverage), 1)) * 100, 2)

        return EvalResult(
            name=fixture["name"],
            schema_valid=schema_valid,
            includes_positive_cases=bool(output.positive_test_cases),
            includes_negative_cases=bool(output.negative_test_cases),
            includes_edge_cases=bool(output.edge_cases),
            includes_api_scenarios=bool(output.api_test_scenarios),
            includes_bug_report=bool(output.bug_report_draft.title),
            guardrails_passed=guardrail_result.passed,
            coverage_score=coverage_score,
            missing_areas=missing_areas,
        )

    @staticmethod
    def _contains_any(text: str, terms: list[str]) -> bool:
        lowered = text.lower()
        return any(term.lower() in lowered for term in terms)
