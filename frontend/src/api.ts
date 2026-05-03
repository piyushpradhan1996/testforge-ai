import type {
  DocumentPayload,
  DocumentSummary,
  EvalRunResponse,
  GeneratePayload,
  Generation,
  GenerationSummary,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function generateQaOutput(payload: GeneratePayload): Promise<Generation> {
  return request<Generation>("/api/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getGenerations(): Promise<GenerationSummary[]> {
  return request<GenerationSummary[]>("/api/generations");
}

export function createDocument(payload: DocumentPayload): Promise<DocumentSummary> {
  return request<DocumentSummary>("/api/documents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getGeneration(id: number): Promise<Generation> {
  return request<Generation>(`/api/generations/${id}`);
}

export function runEvals(): Promise<EvalRunResponse> {
  return request<EvalRunResponse>("/api/evals/run", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getMarkdownExport(id: number): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/generations/${id}/export`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.text();
}
