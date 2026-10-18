import { Task1QueryResponse } from "../types/index.js";

export class KnowledgeBrainClient {
  private baseUrl: string;
  private timeoutMs: number;
  private maxRetries: number;

  constructor(baseUrl = process.env.TASK1_API_URL || "http://127.0.0.1:8000/api/v1", timeoutMs = 5000, maxRetries = 2) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
    this.maxRetries = maxRetries;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`${this.baseUrl}/health`, { signal: controller.signal });
      clearTimeout(id);
      return res.ok;
    } catch {
      return false;
    }
  }

  async queryKnowledge(query: string, includeImages = true): Promise<Task1QueryResponse> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

        const response = await fetch(`${this.baseUrl}/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "User-Agent": "Task2-InboxAgent-Client/1.0"
          },
          body: JSON.stringify({
            query,
            include_images: includeImages,
            top_k: 5
          }),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`Task 1 API returned HTTP status ${response.status}: ${response.statusText}`);
        }

        const data = (await response.json()) as Task1QueryResponse;
        return data;
      } catch (err: any) {
        lastError = err;
        if (attempt < this.maxRetries) {
          await new Promise((r) => setTimeout(r, attempt * 400));
        }
      }
    }

    // Graceful resilient fallback if Task 1 is unreachable
    console.warn(`[KnowledgeClient] Could not reach Task 1 API (${lastError?.message}). Providing fallback response.`);
    return {
      query,
      answer: "The Knowledge Brain service is currently unreachable or timed out. Please verify Task 1 microservice on port 8000.",
      status: "insufficient_evidence",
      confidence: 0.0,
      sources: [],
      images: [],
      needs_escalation: true,
      escalation_id: "ERR-CONN-TASK1"
    };
  }
}

export const knowledgeClient = new KnowledgeBrainClient();
