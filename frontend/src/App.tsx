import { FormEvent, useEffect, useMemo, useState } from "react";
import { generateQaOutput, getGeneration, getGenerations, getMarkdownExport, runEvals } from "./api";
import type { EvalResult, GeneratePayload, Generation, GenerationSummary, TestCase } from "./types";

type View = "generate" | "results" | "history" | "evals";

const emptyForm: GeneratePayload = {
  title: "",
  requirement: "",
  acceptance_criteria: "",
  api_notes: "",
  feature_area: "",
  priority: "Medium",
  supporting_context: "",
};

function App() {
  const [view, setView] = useState<View>(() => (window.location.hash === "#history" ? "history" : "generate"));
  const [form, setForm] = useState<GeneratePayload>(emptyForm);
  const [selectedGeneration, setSelectedGeneration] = useState<Generation | null>(null);
  const [history, setHistory] = useState<GenerationSummary[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isEvalLoading, setIsEvalLoading] = useState(false);
  const [evalResults, setEvalResults] = useState<EvalResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [exportStatus, setExportStatus] = useState<string | null>(null);

  useEffect(() => {
    window.location.hash = view === "generate" ? "" : view;
    if (view === "history") {
      void loadHistory();
    }
  }, [view]);

  async function loadHistory() {
    setIsHistoryLoading(true);
    setError(null);
    try {
      setHistory(await getGenerations());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load history");
    } finally {
      setIsHistoryLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsGenerating(true);
    setError(null);
    setExportStatus(null);

    const payload: GeneratePayload = {
      ...form,
      api_notes: form.api_notes?.trim() || undefined,
      feature_area: form.feature_area?.trim() || undefined,
      priority: form.priority?.trim() || undefined,
      supporting_context: form.supporting_context?.trim() || undefined,
    };

    try {
      const generation = await generateQaOutput(payload);
      setSelectedGeneration(generation);
      setView("results");
      void loadHistory();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to generate QA output");
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleSelectHistory(id: number) {
    setError(null);
    setExportStatus(null);
    try {
      const generation = await getGeneration(id);
      setSelectedGeneration(generation);
      setView("results");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load generation");
    }
  }

  async function handleCopyMarkdown() {
    if (!selectedGeneration) return;
    setExportStatus(null);
    try {
      const markdown = await getMarkdownExport(selectedGeneration.id);
      await navigator.clipboard.writeText(markdown);
      setExportStatus("Markdown copied");
    } catch (caught) {
      setExportStatus(caught instanceof Error ? caught.message : "Unable to copy Markdown");
    }
  }

  async function handleDownloadMarkdown() {
    if (!selectedGeneration) return;
    setExportStatus(null);
    try {
      const markdown = await getMarkdownExport(selectedGeneration.id);
      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${slugify(selectedGeneration.title)}-qa-output.md`;
      link.click();
      URL.revokeObjectURL(link.href);
      setExportStatus("Markdown downloaded");
    } catch (caught) {
      setExportStatus(caught instanceof Error ? caught.message : "Unable to download Markdown");
    }
  }

  async function handleRunEvals() {
    setIsEvalLoading(true);
    setError(null);
    try {
      const response = await runEvals();
      setEvalResults(response.results);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to run evals");
    } finally {
      setIsEvalLoading(false);
    }
  }

  const content = useMemo(() => {
    if (view === "history") {
      return (
        <HistoryPage
          history={history}
          isLoading={isHistoryLoading}
          onRefresh={loadHistory}
          onSelect={handleSelectHistory}
        />
      );
    }

    if (view === "evals") {
      return <EvalDashboard results={evalResults} isLoading={isEvalLoading} onRun={handleRunEvals} />;
    }

    if (view === "results") {
      return selectedGeneration ? (
        <ResultsPage
          generation={selectedGeneration}
          exportStatus={exportStatus}
          onCopyMarkdown={handleCopyMarkdown}
          onDownloadMarkdown={handleDownloadMarkdown}
        />
      ) : (
        <EmptyResults onGenerate={() => setView("generate")} />
      );
    }

    return (
      <GeneratePage
        form={form}
        isGenerating={isGenerating}
        onChange={setForm}
        onSubmit={handleSubmit}
      />
    );
  }, [view, history, isHistoryLoading, selectedGeneration, exportStatus, form, isGenerating, evalResults, isEvalLoading]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="brand" type="button" onClick={() => setView("generate")}>
          <span className="brand-mark">TF</span>
          <span>
            <strong>TestForge AI</strong>
            <small>QA Assistant</small>
          </span>
        </button>
        <nav aria-label="Primary navigation">
          <button className={view === "generate" ? "active" : ""} type="button" onClick={() => setView("generate")}>
            Generate
          </button>
          <button className={view === "history" ? "active" : ""} type="button" onClick={() => setView("history")}>
            History
          </button>
          <button className={view === "evals" ? "active" : ""} type="button" onClick={() => setView("evals")}>
            Evals
          </button>
        </nav>
      </header>

      {error && <div className="alert">{error}</div>}
      {content}
    </main>
  );
}

function GeneratePage({
  form,
  isGenerating,
  onChange,
  onSubmit,
}: {
  form: GeneratePayload;
  isGenerating: boolean;
  onChange: (value: GeneratePayload) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  function update<K extends keyof GeneratePayload>(key: K, value: GeneratePayload[K]) {
    onChange({ ...form, [key]: value });
  }

  return (
    <section className="workspace-grid">
      <form className="input-panel" onSubmit={onSubmit}>
        <div className="section-heading">
          <p>Requirement Input</p>
          <h1>Generate structured QA assets</h1>
        </div>

        <label>
          Title
          <input
            required
            value={form.title}
            onChange={(event) => update("title", event.target.value)}
            placeholder="Checkout discount validation"
          />
        </label>

        <label>
          Requirement / User Story
          <textarea
            required
            rows={6}
            value={form.requirement}
            onChange={(event) => update("requirement", event.target.value)}
            placeholder="As a shopper, I want to apply a valid discount code during checkout..."
          />
        </label>

        <label>
          Acceptance Criteria
          <textarea
            required
            rows={5}
            value={form.acceptance_criteria}
            onChange={(event) => update("acceptance_criteria", event.target.value)}
            placeholder="Valid codes reduce the order total. Expired codes show an error."
          />
        </label>

        <label>
          API Notes / Payload Notes
          <textarea
            rows={4}
            value={form.api_notes}
            onChange={(event) => update("api_notes", event.target.value)}
            placeholder="POST /api/checkout/discount with code and cartId"
          />
        </label>

        <label>
          Supporting docs / API notes / product context
          <textarea
            rows={5}
            value={form.supporting_context}
            onChange={(event) => update("supporting_context", event.target.value)}
            placeholder="Paste release notes, API docs, business rules, or product context that should influence generation."
          />
        </label>

        <div className="field-row">
          <label>
            Feature Area
            <input
              value={form.feature_area}
              onChange={(event) => update("feature_area", event.target.value)}
              placeholder="Checkout"
            />
          </label>
          <label>
            Priority
            <select value={form.priority} onChange={(event) => update("priority", event.target.value)}>
              <option>Critical</option>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </label>
        </div>

        <button className="primary-action" type="submit" disabled={isGenerating}>
          {isGenerating ? "Generating..." : "Generate QA Output"}
        </button>
      </form>

      <aside className="output-preview">
        <h2>Output Sections</h2>
        <ul>
          <li>Positive test cases</li>
          <li>Negative test cases</li>
          <li>Edge cases</li>
          <li>API test scenarios</li>
          <li>Bug report draft</li>
          <li>QA checklist</li>
          <li>RAG context and guardrail checks</li>
        </ul>
      </aside>
    </section>
  );
}

function ResultsPage({
  generation,
  exportStatus,
  onCopyMarkdown,
  onDownloadMarkdown,
}: {
  generation: Generation;
  exportStatus: string | null;
  onCopyMarkdown: () => void;
  onDownloadMarkdown: () => void;
}) {
  return (
    <section className="results-layout">
      <div className="results-header">
        <div>
          <p>Generated {new Date(generation.generated_at).toLocaleString()}</p>
          <h1>{generation.title}</h1>
        </div>
        <div className="action-group">
          <button type="button" onClick={onCopyMarkdown}>
            Copy Markdown
          </button>
          <button type="button" onClick={onDownloadMarkdown}>
            Download .md
          </button>
        </div>
      </div>
      {exportStatus && <div className="status-line">{exportStatus}</div>}

      <TestCaseSection title="Positive Test Cases" cases={generation.positive_test_cases} />
      <TestCaseSection title="Negative Test Cases" cases={generation.negative_test_cases} />
      <TestCaseSection title="Edge Cases" cases={generation.edge_cases} />
      <TestCaseSection title="API Test Scenarios" cases={generation.api_test_scenarios} />

      <section className="result-section">
        <h2>Bug Report Draft</h2>
        <div className="bug-grid">
          <div>
            <h3>{generation.bug_report_draft.title}</h3>
            <p>{generation.bug_report_draft.description}</p>
          </div>
          <dl>
            <dt>Severity</dt>
            <dd>{generation.bug_report_draft.severity}</dd>
            <dt>Environment</dt>
            <dd>{generation.bug_report_draft.environment}</dd>
            <dt>Expected</dt>
            <dd>{generation.bug_report_draft.expected_result}</dd>
            <dt>Actual</dt>
            <dd>{generation.bug_report_draft.actual_result}</dd>
          </dl>
        </div>
        <h3>Steps to Reproduce</h3>
        <ol>
          {generation.bug_report_draft.steps_to_reproduce.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>

      <section className="result-section">
        <h2>QA Checklist</h2>
        <ul className="checklist">
          {generation.qa_checklist.map((item) => (
            <li key={item}>
              <span aria-hidden="true" />
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="result-section">
        <h2>Retrieved Context</h2>
        {generation.retrieved_context?.length ? (
          <div className="context-list">
            {generation.retrieved_context.map((context) => (
              <article className="context-item" key={`${context.document_title}-${context.chunk_index}-${context.id ?? "inline"}`}>
                <strong>{context.document_title}</strong>
                <small>
                  Chunk {context.chunk_index} | Score {context.score}
                </small>
                <p>{context.content}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">No retrieved context was used.</p>
        )}
      </section>

      <section className="result-section metadata-grid">
        <div>
          <h2>Model Metadata</h2>
          <dl>
            <dt>Provider</dt>
            <dd>{generation.model_metadata?.provider ?? "mock"}</dd>
            <dt>Prompt Version</dt>
            <dd>{generation.model_metadata?.prompt_version ?? "qa_generation_v1"}</dd>
            <dt>Used RAG</dt>
            <dd>{String(generation.model_metadata?.used_rag ?? false)}</dd>
            <dt>Retrieved Context</dt>
            <dd>{generation.model_metadata?.retrieved_context_count ?? 0}</dd>
          </dl>
        </div>
        <div>
          <h2>Guardrail Result</h2>
          <p className={generation.guardrail_result?.passed === false ? "guardrail-fail" : "guardrail-pass"}>
            {generation.guardrail_result?.passed === false ? "Needs review" : "Passed"}
          </p>
          <h3>Warnings</h3>
          <StatusList items={generation.guardrail_result?.warnings ?? []} emptyLabel="No warnings" />
          <h3>Errors</h3>
          <StatusList items={generation.guardrail_result?.errors ?? []} emptyLabel="No errors" />
        </div>
      </section>
    </section>
  );
}

function StatusList({ items, emptyLabel }: { items: string[]; emptyLabel: string }) {
  if (items.length === 0) {
    return <p className="muted">{emptyLabel}</p>;
  }
  return (
    <ul>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function TestCaseSection({ title, cases }: { title: string; cases: TestCase[] }) {
  return (
    <section className="result-section">
      <h2>{title}</h2>
      <div className="case-grid">
        {cases.map((testCase) => (
          <article className="case-card" key={testCase.id}>
            <div className="case-card-header">
              <span>{testCase.id}</span>
              <strong>{testCase.title}</strong>
            </div>
            <h3>Preconditions</h3>
            <ul>
              {testCase.preconditions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <h3>Steps</h3>
            <ol>
              {testCase.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <h3>Expected Result</h3>
            <p>{testCase.expected_result}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function HistoryPage({
  history,
  isLoading,
  onRefresh,
  onSelect,
}: {
  history: GenerationSummary[];
  isLoading: boolean;
  onRefresh: () => void;
  onSelect: (id: number) => void;
}) {
  return (
    <section className="history-layout">
      <div className="results-header">
        <div>
          <p>Saved Outputs</p>
          <h1>Generation History</h1>
        </div>
        <button type="button" onClick={onRefresh}>
          Refresh
        </button>
      </div>

      {isLoading && <div className="status-line">Loading history...</div>}

      <div className="history-list">
        {history.map((item) => (
          <button className="history-item" key={item.id} type="button" onClick={() => onSelect(item.id)}>
            <span>
              <strong>{item.title}</strong>
              <small>{new Date(item.generated_at).toLocaleString()}</small>
            </span>
            <span className="counts">
              {item.positive_count + item.negative_count + item.edge_count + item.api_count} scenarios
            </span>
          </button>
        ))}
      </div>

      {!isLoading && history.length === 0 && <div className="empty-state">No generated outputs yet.</div>}
    </section>
  );
}

function EvalDashboard({
  results,
  isLoading,
  onRun,
}: {
  results: EvalResult[];
  isLoading: boolean;
  onRun: () => void;
}) {
  return (
    <section className="history-layout">
      <div className="results-header">
        <div>
          <p>Evaluation Harness</p>
          <h1>LLM QA Evals</h1>
        </div>
        <button type="button" onClick={onRun} disabled={isLoading}>
          {isLoading ? "Running..." : "Run Evals"}
        </button>
      </div>

      <div className="eval-grid">
        {results.map((result) => (
          <article className="eval-card" key={result.name}>
            <div className="eval-score">{result.coverage_score}%</div>
            <h2>{result.name}</h2>
            <dl>
              <dt>Schema Valid</dt>
              <dd>{String(result.schema_valid)}</dd>
              <dt>Guardrails Passed</dt>
              <dd>{String(result.guardrails_passed)}</dd>
              <dt>Missing Areas</dt>
              <dd>{result.missing_areas.length ? result.missing_areas.join(", ") : "None"}</dd>
            </dl>
          </article>
        ))}
      </div>

      {!isLoading && results.length === 0 && <div className="empty-state">Run evals to score the mock LLM output.</div>}
    </section>
  );
}

function EmptyResults({ onGenerate }: { onGenerate: () => void }) {
  return (
    <section className="empty-state">
      <h1>No result selected</h1>
      <button type="button" onClick={onGenerate}>
        Open Generator
      </button>
    </section>
  );
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default App;
