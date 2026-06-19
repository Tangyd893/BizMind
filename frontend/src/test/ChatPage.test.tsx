import { describe, beforeEach, afterEach, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPage from "../pages/ChatPage";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock crypto.randomUUID
beforeEach(() => {
  let counter = 0;
  vi.stubGlobal("crypto", {
    randomUUID: vi.fn(() => `test-uuid-${counter++}`),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ChatPage", () => {
  it("renders mode toggle and empty state", () => {
    render(<ChatPage />);
    expect(screen.getByText("Agent")).toBeDefined();
    expect(screen.getByText("Baseline")).toBeDefined();
    expect(screen.getByPlaceholderText("输入问题…")).toBeDefined();
  });

  it("renders the new thread button", () => {
    render(<ChatPage />);
    expect(screen.getByText("+ 新建会话")).toBeDefined();
  });

  it("disables send button when input is empty", () => {
    render(<ChatPage />);
    const sendButton = screen.getByText("发送");
    expect(sendButton).toBeDefined();
    expect((sendButton as HTMLButtonElement).disabled).toBe(true);
  });

  it("enables send button when input has text", async () => {
    const user = userEvent.setup();
    render(<ChatPage />);
    const input = screen.getByPlaceholderText("输入问题…");
    await user.type(input, "Hello");
    const sendButton = screen.getByText("发送");
    expect((sendButton as HTMLButtonElement).disabled).toBe(false);
  });

  it("clears input after typing and clicking clear would reset — just verify controlled input works", async () => {
    const user = userEvent.setup();
    render(<ChatPage />);
    const input = screen.getByPlaceholderText("输入问题…") as HTMLInputElement;
    await user.type(input, "Test message");
    expect(input.value).toBe("Test message");
  });
});
