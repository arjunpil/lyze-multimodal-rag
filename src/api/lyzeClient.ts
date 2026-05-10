// src/api/lyzeClient.ts
// Talks to the Lyze FastAPI backend at localhost:8000

const BASE_URL = "http://localhost:8000";

export interface Source {
  citation: string;
  modality: string;
  source: string;
  score: number;
  preview: string;
  metadata: Record<string, unknown>;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
}

export interface IngestResponse {
  filename: string;
  chunks: number;
  total: number;
  message?: string;
}

export interface StatsResponse {
  total_chunks: number;
  status: string;
}

// Check if the backend is running
export async function checkBackend(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/`, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

// Get vector store stats
export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${BASE_URL}/stats`);
  if (!res.ok) throw new Error("Failed to get stats");
  return res.json();
}

// Ingest a single file
export async function ingestFile(
  file: File,
  onProgress?: (msg: string) => void
): Promise<IngestResponse> {
  onProgress?.(`Uploading ${file.name}...`);
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE_URL}/ingest`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }

  const data: IngestResponse = await res.json();
  onProgress?.(`✓ ${file.name} — ${data.chunks} chunks indexed`);
  return data;
}

// Ingest multiple files sequentially
export async function ingestFiles(
  files: File[],
  onProgress?: (msg: string) => void
): Promise<{ total: number; results: IngestResponse[] }> {
  const results: IngestResponse[] = [];
  let total = 0;

  for (const file of files) {
    try {
      const result = await ingestFile(file, onProgress);
      results.push(result);
      total = result.total;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      onProgress?.(`✗ ${file.name} — ${msg}`);
    }
  }

  onProgress?.(`\nDone — ${total} total chunks in store.`);
  return { total, results };
}

// Query the RAG pipeline
export async function queryRAG(
  question: string,
  options?: {
    top_k?: number;
    modality_filter?: string | null;
  }
): Promise<QueryResponse> {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      top_k: options?.top_k ?? 5,
      modality_filter: options?.modality_filter ?? null,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Query failed" }));
    throw new Error(err.detail || "Query failed");
  }

  return res.json();
}

// Clear all documents from the store
export async function clearStore(): Promise<void> {
  const res = await fetch(`${BASE_URL}/clear`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear store");
}
