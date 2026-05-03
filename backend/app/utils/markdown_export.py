from app.schemas import BugReportDraft, GenerationResponse, TestCase


def _test_case_block(test_case: TestCase) -> str:
    preconditions = "\n".join(f"  - {item}" for item in test_case.preconditions)
    steps = "\n".join(f"  {index}. {step}" for index, step in enumerate(test_case.steps, start=1))
    return (
        f"### {test_case.id}: {test_case.title}\n\n"
        f"- Type: {test_case.type}\n"
        f"- Preconditions:\n{preconditions}\n"
        f"- Steps:\n{steps}\n"
        f"- Expected Result: {test_case.expected_result}\n"
    )


def _test_case_section(title: str, cases: list[TestCase]) -> str:
    blocks = "\n".join(_test_case_block(case) for case in cases)
    return f"## {title}\n\n{blocks}".strip()


def _bug_report_section(bug: BugReportDraft) -> str:
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(bug.steps_to_reproduce, start=1))
    return f"""## Bug Report Draft

### {bug.title}

- Severity: {bug.severity}
- Environment: {bug.environment}

**Description**

{bug.description}

**Steps to Reproduce**

{steps}

**Expected Result**

{bug.expected_result}

**Actual Result**

{bug.actual_result}
""".strip()


def _retrieved_context_section(generation: GenerationResponse) -> str:
    if not generation.retrieved_context:
        return "## Retrieved Context\n\nNo retrieved context was used."

    items = "\n\n".join(
        (
            f"### {context.document_title} (chunk {context.chunk_index}, score {context.score})\n\n"
            f"{context.content}"
        )
        for context in generation.retrieved_context
    )
    return f"## Retrieved Context\n\n{items}"


def _metadata_section(generation: GenerationResponse) -> str:
    metadata = generation.model_metadata
    guardrails = generation.guardrail_result
    warnings = "\n".join(f"- {warning}" for warning in guardrails.warnings) or "- None"
    errors = "\n".join(f"- {error}" for error in guardrails.errors) or "- None"
    return f"""## Model Metadata

- Provider: {metadata.provider}
- Prompt Version: {metadata.prompt_version}
- Used RAG: {metadata.used_rag}
- Retrieved Context Count: {metadata.retrieved_context_count}

## Guardrail Result

- Passed: {guardrails.passed}

**Warnings**

{warnings}

**Errors**

{errors}
""".strip()


def generation_to_markdown(generation: GenerationResponse) -> str:
    checklist = "\n".join(f"- [ ] {item}" for item in generation.qa_checklist)
    return f"""# {generation.title}

Generated at: {generation.generated_at.isoformat()}

{_test_case_section("Positive Test Cases", generation.positive_test_cases)}

{_test_case_section("Negative Test Cases", generation.negative_test_cases)}

{_test_case_section("Edge Cases", generation.edge_cases)}

{_test_case_section("API Test Scenarios", generation.api_test_scenarios)}

{_bug_report_section(generation.bug_report_draft)}

## QA Checklist

{checklist}

{_retrieved_context_section(generation)}

{_metadata_section(generation)}
""".strip() + "\n"
