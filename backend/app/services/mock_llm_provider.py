import os
import re

from app.schemas import BugReportDraft, GeneratedQAOutput, GenerateRequest, ModelMetadata, RetrievedContext, TestCase
from app.services.llm_provider import LLMProvider, load_prompt


def _compact(text: str | None, fallback: str) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned or fallback


def _shorten(text: str, limit: int = 110) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _criteria_items(criteria: str) -> list[str]:
    raw_items = re.split(r"(?:\r?\n|;|\.\s+)", criteria)
    items = []
    for item in raw_items:
        cleaned = re.sub(r"^[-*\d.)\s]+", "", item.strip())
        if cleaned:
            items.append(cleaned)
    return items[:4] or [_compact(criteria, "Acceptance criteria are documented")]


def _severity(priority: str | None) -> str:
    normalized = (priority or "").strip().lower()
    if normalized in {"critical", "p0", "blocker"}:
        return "Critical"
    if normalized in {"high", "p1"}:
        return "High"
    if normalized in {"low", "p3"}:
        return "Low"
    return "Medium"


def _context_summary(retrieved_context: list[RetrievedContext]) -> str:
    if not retrieved_context:
        return "No retrieved context was used"
    top = retrieved_context[0]
    return _shorten(f"{top.document_title}: {top.content}", 150)


class MockLLMProvider(LLMProvider):
    """Deterministic provider that creates useful QA assets without API keys."""

    def generate(
        self,
        request: GenerateRequest,
        retrieved_context: list[RetrievedContext] | None = None,
    ) -> GeneratedQAOutput:
        prompt_version = os.getenv("PROMPT_VERSION", "qa_generation_v1")
        load_prompt(f"{prompt_version}.txt")

        context = retrieved_context or []
        title = _compact(request.title, "Untitled requirement")
        feature = _compact(request.feature_area, title)
        requirement = _shorten(_compact(request.requirement, title), 150)
        criteria = _criteria_items(request.acceptance_criteria)
        first_criterion = _shorten(criteria[0], 120)
        api_notes = _compact(request.api_notes, "No API notes were supplied")
        severity = _severity(request.priority)
        context_hint = _context_summary(context)

        positive_cases = [
            TestCase(
                id="POS-001",
                title=f"Verify successful {title} flow with valid inputs",
                preconditions=[
                    f"The {feature} feature is available in the test environment",
                    "A tester has valid access and clean test data",
                ],
                steps=[
                    f"Open the {feature} workflow",
                    f"Complete the flow using data that satisfies: {requirement}",
                    "Submit or save the changes",
                    "Review the confirmation message, stored data, and generated output",
                ],
                expected_result=f"The flow completes successfully and satisfies: {first_criterion}",
                type="positive",
            ),
            TestCase(
                id="POS-002",
                title=f"Verify acceptance criteria are reflected for {title}",
                preconditions=[f"Acceptance criteria are available for {feature}", f"Context considered: {context_hint}"],
                steps=[
                    "Execute the happy path using representative user data",
                    f"Check the behavior against this criterion: {first_criterion}",
                    "Confirm the UI, API response, and persisted state are aligned",
                ],
                expected_result="All visible behavior and saved data match the acceptance criteria and supporting context",
                type="positive",
            ),
            TestCase(
                id="POS-003",
                title=f"Verify {title} supports repeatable successful submissions",
                preconditions=["A previous successful run exists for comparison"],
                steps=[
                    "Run the same valid scenario twice with separate test records",
                    "Compare confirmation details and generated records",
                    "Confirm no duplicate or stale data appears in the second result",
                ],
                expected_result=f"Each successful {feature} submission creates an accurate independent result",
                type="positive",
            ),
        ]

        negative_cases = [
            TestCase(
                id="NEG-001",
                title=f"Verify {title} rejects missing required information",
                preconditions=[f"The tester is on the {feature} entry point"],
                steps=[
                    "Leave one required field blank",
                    "Submit the form or API request",
                    "Review validation messaging and saved records",
                ],
                expected_result="The request is blocked, a clear validation message is shown, and no invalid record is saved",
                type="negative",
            ),
            TestCase(
                id="NEG-002",
                title=f"Verify invalid data does not satisfy {title}",
                preconditions=["Validation rules and expected formats are known"],
                steps=[
                    "Enter values with invalid format, unsupported status, or conflicting details",
                    "Submit the invalid scenario",
                    "Inspect UI feedback, API status, and logs",
                ],
                expected_result=f"The system rejects invalid data for {feature} without partial updates",
                type="negative",
            ),
            TestCase(
                id="NEG-003",
                title=f"Verify unauthorized access is prevented for {title}",
                preconditions=["A user without the required permission is available"],
                steps=[
                    f"Attempt to access the {feature} action as an unauthorized user",
                    "Try to submit valid-looking data",
                    "Check the response, audit trail, and stored data",
                ],
                expected_result="Access is denied and no protected data is exposed or changed",
                type="negative",
            ),
        ]

        edge_cases = [
            TestCase(
                id="EDGE-001",
                title=f"Verify boundary length handling for {title}",
                preconditions=["Field length limits are documented or can be inferred"],
                steps=[
                    "Submit values at the minimum accepted length",
                    "Submit values at the maximum accepted length",
                    "Submit values just beyond the maximum length",
                ],
                expected_result="Boundary values are handled consistently and over-limit data is rejected clearly",
                type="edge",
            ),
            TestCase(
                id="EDGE-002",
                title=f"Verify duplicate or retry behavior for {title}",
                preconditions=["Network throttling or request replay tooling is available"],
                steps=[
                    "Submit a valid request",
                    "Immediately retry the same request or refresh after submission",
                    "Review duplicate prevention, idempotency, and user messaging",
                ],
                expected_result=f"The {feature} flow avoids duplicate side effects and communicates the final state",
                type="edge",
            ),
            TestCase(
                id="EDGE-003",
                title=f"Verify special characters and whitespace for {title}",
                preconditions=["Input fields accept user-entered text"],
                steps=[
                    "Enter leading and trailing spaces, punctuation, and unicode-like business text",
                    "Submit the scenario",
                    "Review displayed values, saved values, and exported values",
                ],
                expected_result="Text is sanitized or preserved according to requirements without broken formatting",
                type="edge",
            ),
        ]

        api_scenarios = [
            TestCase(
                id="API-001",
                title=f"Verify API contract for {title}",
                preconditions=[f"API notes: {_shorten(api_notes, 140)}"],
                steps=[
                    "Send a valid request using the documented payload and headers",
                    "Validate status code, response schema, and response body values",
                    "Confirm the server-side record matches the API response",
                ],
                expected_result="The API returns a successful response with the expected schema and persisted state",
                type="api",
            ),
            TestCase(
                id="API-002",
                title=f"Verify API validation errors for {title}",
                preconditions=["An API client such as curl, Postman, or Playwright request is available"],
                steps=[
                    "Remove a required payload field",
                    "Send a request with an invalid data type",
                    "Send a request with malformed JSON or unsupported content type",
                ],
                expected_result="The API returns a 4xx response with actionable validation details and no data corruption",
                type="api",
            ),
            TestCase(
                id="API-003",
                title=f"Verify API observability for {title}",
                preconditions=["Application logs or request tracing are available"],
                steps=[
                    "Trigger one successful API request",
                    "Trigger one validation failure",
                    "Review request IDs, log messages, and error handling",
                ],
                expected_result="Success and failure paths are observable without exposing secrets or sensitive payload values",
                type="api",
            ),
        ]

        bug_report = BugReportDraft(
            title=f"{title} does not satisfy acceptance criterion",
            description=(
                f"During testing of {feature}, the behavior did not match the expected requirement: "
                f"{first_criterion}"
            ),
            steps_to_reproduce=[
                f"Navigate to or call the {feature} workflow",
                f"Use test data based on: {requirement}",
                "Submit the scenario",
                "Compare the result with the documented acceptance criteria and retrieved context",
            ],
            expected_result=f"The system should satisfy: {first_criterion}",
            actual_result="Actual result placeholder: describe the observed mismatch, error, or missing behavior.",
            severity=severity,
            environment="Environment placeholder: browser/API client, build version, test data, and database state.",
        )

        checklist = [
            f"Confirm the main {feature} happy path satisfies documented acceptance criteria",
            "Verify required-field validation and invalid-format handling",
            "Test permission, authentication, and authorization behavior where applicable",
            "Exercise boundary values, duplicate submissions, retries, and refresh behavior",
            "Validate API status codes, response schema, and persistence when API notes apply",
            "Check that user-facing messages are clear, actionable, and consistent",
            "Review logs for useful diagnostics without sensitive data exposure",
            "Attach evidence: screenshots, API responses, test data, and environment details",
        ]

        for criterion in criteria[1:]:
            checklist.append(f"Confirm acceptance criterion: {_shorten(criterion, 140)}")

        return GeneratedQAOutput(
            positive_test_cases=positive_cases,
            negative_test_cases=negative_cases,
            edge_cases=edge_cases,
            api_test_scenarios=api_scenarios,
            bug_report_draft=bug_report,
            qa_checklist=checklist,
            retrieved_context=context,
            model_metadata=ModelMetadata(
                provider="mock",
                prompt_version=prompt_version,
                used_rag=bool(context),
                retrieved_context_count=len(context),
            ),
        )
