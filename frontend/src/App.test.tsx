import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import type { Generation, GenerationSummary } from "./types";

const generatedOutput: Generation = {
  id: 7,
  title: "Checkout discount validation",
  generated_at: "2026-05-03T01:00:00.000Z",
  positive_test_cases: [
    {
      id: "POS-001",
      title: "Verify successful Checkout discount validation flow with valid inputs",
      preconditions: ["The Checkout feature is available"],
      steps: ["Open checkout", "Apply SAVE10", "Submit the order"],
      expected_result: "The discount is applied before payment",
      type: "positive",
    },
  ],
  negative_test_cases: [
    {
      id: "NEG-001",
      title: "Verify expired discount code is rejected",
      preconditions: ["An expired code exists"],
      steps: ["Open checkout", "Apply EXPIRED10"],
      expected_result: "A validation error is shown and the total is unchanged",
      type: "negative",
    },
  ],
  edge_cases: [
    {
      id: "EDGE-001",
      title: "Verify duplicate discount submission",
      preconditions: ["Checkout page is open"],
      steps: ["Apply the same code twice"],
      expected_result: "Only one discount is applied",
      type: "edge",
    },
  ],
  api_test_scenarios: [
    {
      id: "API-001",
      title: "Verify discount API contract",
      preconditions: ["POST /api/checkout/discount is available"],
      steps: ["Send code and cartId", "Validate response schema"],
      expected_result: "The response includes adjustedTotal and discountAmount",
      type: "api",
    },
  ],
  bug_report_draft: {
    title: "Checkout discount validation does not satisfy acceptance criterion",
    description: "Discount total is not visible before payment.",
    steps_to_reproduce: ["Open checkout", "Apply SAVE10", "Review order total"],
    expected_result: "Discount total is visible before payment.",
    actual_result: "Actual result placeholder.",
    severity: "High",
    environment: "Environment placeholder.",
  },
  qa_checklist: ["Confirm valid codes reduce the order total"],
  retrieved_context: [
    {
      id: 1,
      document_title: "Checkout Discount Rules",
      chunk_index: 0,
      content: "Expired discount codes are rejected before payment.",
      score: 0.75,
    },
  ],
  model_metadata: {
    provider: "mock",
    prompt_version: "qa_generation_v1",
    used_rag: true,
    retrieved_context_count: 1,
  },
  guardrail_result: {
    passed: true,
    warnings: [],
    errors: [],
  },
};

const history: GenerationSummary[] = [
  {
    id: generatedOutput.id,
    title: generatedOutput.title,
    generated_at: generatedOutput.generated_at,
    positive_count: 1,
    negative_count: 1,
    edge_count: 1,
    api_count: 1,
  },
];

function jsonResponse(body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function textResponse(body: string) {
  return Promise.resolve(new Response(body, { status: 200, headers: { "Content-Type": "text/markdown" } }));
}

function mockApi() {
  return vi.fn((input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/api/generate")) return jsonResponse(generatedOutput);
    if (url.endsWith("/api/documents")) {
      return jsonResponse({
        id: 1,
        title: "Checkout supporting context",
        source_type: "inline_generation_context",
        chunk_count: 1,
        created_at: "2026-05-03T01:00:00.000Z",
      });
    }
    if (url.endsWith("/api/evals/run")) {
      return jsonResponse({
        provider: "mock",
        prompt_version: "qa_generation_v1",
        results: [
          {
            name: "Payment API Requirement",
            schema_valid: true,
            includes_positive_cases: true,
            includes_negative_cases: true,
            includes_edge_cases: true,
            includes_api_scenarios: true,
            includes_bug_report: true,
            guardrails_passed: true,
            coverage_score: 100,
            missing_areas: [],
          },
        ],
      });
    }
    if (url.endsWith("/api/generations")) return jsonResponse(history);
    if (url.endsWith(`/api/generations/${generatedOutput.id}`)) return jsonResponse(generatedOutput);
    if (url.endsWith(`/api/generations/${generatedOutput.id}/export`)) {
      return textResponse("# Checkout discount validation\n\n## Positive Test Cases\n");
    }
    return Promise.resolve(new Response("Not found", { status: 404 }));
  });
}

beforeEach(() => {
  window.location.hash = "";
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("renders the requirement input form", () => {
    vi.stubGlobal("fetch", mockApi());

    render(<App />);

    expect(screen.getByRole("heading", { name: /generate structured qa assets/i })).toBeTruthy();
    expect(screen.getByLabelText(/title/i)).toBeTruthy();
    expect(screen.getByLabelText(/requirement/i)).toBeTruthy();
    expect(screen.getByLabelText(/acceptance criteria/i)).toBeTruthy();
    expect(screen.getByText("API test scenarios")).toBeTruthy();
  });

  it("submits requirements and displays structured results", async () => {
    const fetchMock = mockApi();
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    fireEvent.change(screen.getByLabelText(/title/i), {
      target: { value: "Checkout discount validation" },
    });
    fireEvent.change(screen.getByLabelText(/requirement/i), {
      target: { value: "As a shopper, I want to apply a valid discount code." },
    });
    fireEvent.change(screen.getByLabelText(/acceptance criteria/i), {
      target: { value: "Valid codes reduce the order total." },
    });
    fireEvent.change(screen.getByPlaceholderText("POST /api/checkout/discount with code and cartId"), {
      target: { value: "POST /api/checkout/discount" },
    });

    fireEvent.click(screen.getByRole("button", { name: /generate qa output/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: generatedOutput.title })).toBeTruthy();
    });
    expect(screen.getByText("POS-001")).toBeTruthy();
    expect(screen.getByText("NEG-001")).toBeTruthy();
    expect(screen.getByText("EDGE-001")).toBeTruthy();
    expect(screen.getByText("API-001")).toBeTruthy();
    expect(screen.getByText("Confirm valid codes reduce the order total")).toBeTruthy();
    expect(screen.getByText("Checkout Discount Rules")).toBeTruthy();
    expect(screen.getByText("Model Metadata")).toBeTruthy();
    expect(screen.getByText("Guardrail Result")).toBeTruthy();

    const generateCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/api/generate"));
    expect(generateCall).toBeTruthy();
    expect(JSON.parse(String(generateCall?.[1]?.body))).toMatchObject({
      title: generatedOutput.title,
      priority: "Medium",
    });
  });

  it("loads history and opens a saved generation", async () => {
    vi.stubGlobal("fetch", mockApi());
    window.location.hash = "#history";

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(generatedOutput.title)).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: /checkout discount validation/i }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: generatedOutput.title })).toBeTruthy();
    });
    expect(screen.getByText("Bug Report Draft")).toBeTruthy();
  });

  it("copies Markdown export from the results page", async () => {
    vi.stubGlobal("fetch", mockApi());

    render(<App />);

    fireEvent.change(screen.getByLabelText(/title/i), {
      target: { value: "Checkout discount validation" },
    });
    fireEvent.change(screen.getByLabelText(/requirement/i), {
      target: { value: "As a shopper, I want to apply a valid discount code." },
    });
    fireEvent.change(screen.getByLabelText(/acceptance criteria/i), {
      target: { value: "Valid codes reduce the order total." },
    });
    fireEvent.click(screen.getByRole("button", { name: /generate qa output/i }));

    await screen.findByRole("button", { name: /copy markdown/i });
    fireEvent.click(screen.getByRole("button", { name: /copy markdown/i }));

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        "# Checkout discount validation\n\n## Positive Test Cases\n",
      );
    });
  });

  it("runs evals from the dashboard", async () => {
    vi.stubGlobal("fetch", mockApi());

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /evals/i }));
    fireEvent.click(screen.getByRole("button", { name: /run evals/i }));

    await waitFor(() => {
      expect(screen.getByText("Payment API Requirement")).toBeTruthy();
    });
    expect(screen.getByText("100%")).toBeTruthy();
    expect(screen.getByText("None")).toBeTruthy();
  });
});
