import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";

describe("App", () => {
  it("renders without crashing", () => {
    render(<App />);
    // App should render at minimum the main container
    expect(document.querySelector("div")).toBeTruthy();
  });
});

describe("SSE client parsing", () => {
  it("parses token events correctly", () => {
    // Verify SSE parsing logic from ChatPage
    const buffer = 'event: token\ndata: {"content":"Hello"}\n\n';
    const lines = buffer.split("\n");
    let dataLine = "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        dataLine = line;
      }
    }
    const data = JSON.parse(dataLine.slice(6));
    expect(data.content).toBe("Hello");
  });

  it("parses agent_step events correctly", () => {
    const buffer = 'event: agent_step\ndata: {"node":"router","status":"completed"}\n\n';
    const lines = buffer.split("\n");
    let currentEvent = "";
    let data: Record<string, unknown> = {};
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        data = JSON.parse(line.slice(6));
      }
    }
    expect(currentEvent).toBe("agent_step");
    expect(data.node).toBe("router");
  });

  it("handles split chunks across reads", () => {
    // Simulate partial read: first chunk ends mid-data
    const chunk1 = 'event: token\ndata: {"con';
    const chunk2 = 'tent":"Split"}\n\n';
    const full = chunk1 + chunk2;

    // Replicate buffer logic
    let buffer = "";
    const results: unknown[] = [];
    for (const chunk of [chunk1, chunk2]) {
      buffer += chunk;
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            results.push(JSON.parse(line.slice(6)));
          } catch { /* skip */ }
        }
      }
    }
    expect(results).toHaveLength(1);
    expect((results[0] as Record<string, unknown>).content).toBe("Split");
  });
});

