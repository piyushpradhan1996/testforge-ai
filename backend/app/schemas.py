from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    requirement: str = Field(..., min_length=5)
    acceptance_criteria: str = Field(..., min_length=3)
    api_notes: str | None = None
    feature_area: str | None = None
    priority: str | None = None
    supporting_context: str | None = None


class TestCase(BaseModel):
    id: str
    title: str
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    type: Literal["positive", "negative", "edge", "api"]


class BugReportDraft(BaseModel):
    title: str
    description: str
    steps_to_reproduce: list[str]
    expected_result: str
    actual_result: str
    severity: str
    environment: str


class RetrievedContext(BaseModel):
    id: int | None = None
    document_title: str
    chunk_index: int
    content: str
    score: float = 0.0


class ModelMetadata(BaseModel):
    provider: str = "mock"
    prompt_version: str = "qa_generation_v1"
    used_rag: bool = False
    retrieved_context_count: int = 0


class GuardrailResult(BaseModel):
    passed: bool = True
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class GeneratedQAOutput(BaseModel):
    positive_test_cases: list[TestCase]
    negative_test_cases: list[TestCase]
    edge_cases: list[TestCase]
    api_test_scenarios: list[TestCase]
    bug_report_draft: BugReportDraft
    qa_checklist: list[str]
    retrieved_context: list[RetrievedContext] = Field(default_factory=list)
    model_metadata: ModelMetadata = Field(default_factory=ModelMetadata)
    guardrail_result: GuardrailResult = Field(default_factory=GuardrailResult)


class GenerationResponse(GeneratedQAOutput):
    id: int
    title: str
    generated_at: datetime


class GenerationSummary(BaseModel):
    id: int
    title: str
    generated_at: datetime
    positive_count: int
    negative_count: int
    edge_count: int
    api_count: int


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    content: str = Field(..., min_length=10)
    filename: str | None = None
    source_type: str | None = "pasted_text"


class DocumentSummary(BaseModel):
    id: int
    title: str
    filename: str | None = None
    source_type: str
    chunk_count: int
    created_at: datetime


class EvalRunRequest(BaseModel):
    use_rag: bool = False


class EvalResult(BaseModel):
    name: str
    schema_valid: bool
    includes_positive_cases: bool
    includes_negative_cases: bool
    includes_edge_cases: bool
    includes_api_scenarios: bool
    includes_bug_report: bool
    guardrails_passed: bool
    coverage_score: float
    missing_areas: list[str]


class EvalRunResponse(BaseModel):
    provider: str
    prompt_version: str
    results: list[EvalResult]
