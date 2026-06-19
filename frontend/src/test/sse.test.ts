/**
 * SSE client-side tests — mock fetch to simulate streaming responses.
 * Tests the SSE parsing logic from the ChatPage component and streamChat client.
 */
import { describe, beforeEach, afterEach, expect, it, vi } from "vitest";

// Replicate the SSE parsing logic from ChatPage for pure testing
function parseSSEEvents(
  chunks: string[],
): Array<{ event: string; data: Record<string, unknown> }> {
  const results: Array<{ event: string; data: Record<string, unknown> }> = [];
  let buffer = "";

  for (const chunk of chunks) {
    buffer += chunk;
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          results.push({ event: currentEvent, data });
        } catch {
          // skip malformed
        }
      }
    }
  }

  return results;
}

describe("SSE parsing", () => {
  it("parses a single token event", () => {
    const events = parseSSEEvents([
      'event: token\ndata: {"content":"Hello"}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("token");
    expect(events[0].data.content).toBe("Hello");
  });

  it("parses multiple events from one chunk", () => {
    const events = parseSSEEvents([
      'event: agent_step\ndata: {"node":"router","status":"completed"}\n\n' +
      'event: token\ndata: {"content":" World"}\n\n',
    ]);
    expect(events).toHaveLength(2);
    expect(events[0].event).toBe("agent_step");
    expect(events[0].data.node).toBe("router");
    expect(events[1].event).toBe("token");
    expect(events[1].data.content).toBe(" World");
  });

  it("parses agent_step with node data", () => {
    const events = parseSSEEvents([
      'event: agent_step\ndata: {"node":"retrieve","status":"completed"}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].data.node).toBe("retrieve");
    expect(events[0].data.status).toBe("completed");
  });

  it("parses done event with route and latency", () => {
    const events = parseSSEEvents([
      'event: done\ndata: {"message_id":"abc-123","route":"rag","retrieval_attempts":1,"total_latency_ms":850}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("done");
    expect(events[0].data.message_id).toBe("abc-123");
    expect(events[0].data.route).toBe("rag");
    expect(events[0].data.total_latency_ms).toBe(850);
  });

  it("parses error event", () => {
    const events = parseSSEEvents([
      'event: error\ndata: {"code":"INTERNAL_ERROR","message":"Something went wrong"}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("error");
    expect(events[0].data.code).toBe("INTERNAL_ERROR");
  });

  it("handles split chunks (partial line buffering)", () => {
    // First chunk: incomplete event
    const events = parseSSEEvents([
      'event: token\ndata: {"con',
      'tent":"Split message"}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].data.content).toBe("Split message");
  });

  it("handles citation event", () => {
    const events = parseSSEEvents([
      'event: citation\ndata: {"source":"doc.md","text_preview":"Some text..."}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe("citation");
    expect(events[0].data.source).toBe("doc.md");
  });

  it("skips malformed data gracefully", () => {
    const events = parseSSEEvents([
      'event: token\ndata: {invalid json}\n\n',
      'event: token\ndata: {"content":"valid"}\n\n',
    ]);
    expect(events).toHaveLength(1);
    expect(events[0].data.content).toBe("valid");
  });

  it("handles empty input", () => {
    const events = parseSSEEvents([]);
    expect(events).toHaveLength(0);
  });
});

describe("streamChat", () => {
  it("sends correct request with agent mode and auth header", async () => {
    // Mock localStorage
    const mockToken = "test-jwt-token";
    const getItemSpy = vi.fn(() => mockToken);
    const origGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = getItemSpy;

    // Mock fetch
    const mockFetch = vi.fn(() =>
      Promise.resolve(new Response(null, { status: 200 }))
    );
    vi.stubGlobal("fetch", mockFetch);

    try {
      const { streamChat } = await import("../api/client");
      await streamChat("thread-1", "Hello", "agent");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/chat/agent/stream");
      expect(options.method).toBe("POST");
      expect(options.headers).toBeDefined();
      const body = JSON.parse(options.body as string);
      expect(body.thread_id).toBe("thread-1");
      expect(body.message).toBe("Hello");
    } finally {
      Storage.prototype.getItem = origGetItem;
      vi.unstubAllGlobals();
    }
  });

  it("sends baseline mode correctly", async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve(new Response(null, { status: 200 }))
    );
    vi.stubGlobal("fetch", mockFetch);

    try {
      const { streamChat } = await import("../api/client");
      await streamChat("thread-2", "Question", "baseline");

      const [url] = mockFetch.mock.calls[0] as [string];
      expect(url).toContain("/chat/baseline/stream");
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
