export type GeneratePayload = {
  title: string;
  requirement: string;
  acceptance_criteria: string;
  api_notes?: string;
  feature_area?: string;
  priority?: string;
  supporting_context?: string;
};

export type TestCase = {
  id: string;
  title: string;
  preconditions: string[];
  steps: string[];
  expected_result: string;
  type: "positive" | "negative" | "edge" | "api";
};

export type BugReportDraft = {
  title: string;
  description: string;
  steps_to_reproduce: string[];
  expected_result: string;
  actual_result: string;
  severity: string;
  environment: string;
};

export type RetrievedContext = {
  id?: number | null;
  document_title: string;
  chunk_index: number;
  content: string;
  score: number;
};

export type ModelMetadata = {
  provider: string;
  prompt_version: string;
  used_rag: boolean;
  retrieved_context_count: number;
};

export type GuardrailResult = {
  passed: boolean;
  warnings: string[];
  errors: string[];
};

export type Generation = {
  id: number;
  title: string;
  generated_at: string;
  positive_test_cases: TestCase[];
  negative_test_cases: TestCase[];
  edge_cases: TestCase[];
  api_test_scenarios: TestCase[];
  bug_report_draft: BugReportDraft;
  qa_checklist: string[];
  retrieved_context?: RetrievedContext[];
  model_metadata?: ModelMetadata;
  guardrail_result?: GuardrailResult;
};

export type GenerationSummary = {
  id: number;
  title: string;
  generated_at: string;
  positive_count: number;
  negative_count: number;
  edge_count: number;
  api_count: number;
};

export type DocumentPayload = {
  title: string;
  content: string;
  filename?: string;
  source_type?: string;
};

export type DocumentSummary = {
  id: number;
  title: string;
  filename?: string | null;
  source_type: string;
  chunk_count: number;
  created_at: string;
};

export type EvalResult = {
  name: string;
  schema_valid: boolean;
  includes_positive_cases: boolean;
  includes_negative_cases: boolean;
  includes_edge_cases: boolean;
  includes_api_scenarios: boolean;
  includes_bug_report: boolean;
  guardrails_passed: boolean;
  coverage_score: number;
  missing_areas: string[];
};

export type EvalRunResponse = {
  provider: string;
  prompt_version: string;
  results: EvalResult[];
};
