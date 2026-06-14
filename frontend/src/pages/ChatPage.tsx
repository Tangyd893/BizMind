import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api/client";
import type { MessageItem, ThreadItem } from "../api/client";

export default function ChatPage() {
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [mode, setMode] = useState<"agent" | "baseline">("agent");
  const [agentStep, setAgentStep] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);

  // Fetch threads
  const loadThreads = useCallback(async () => {
    try {
      const data = await api.fetchThreads();
      setThreads(data.items);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  // Fetch messages when switching thread
  useEffect(() => {
    if (!activeThreadId) return;
    api.fetchMessages(activeThreadId).then((data) => {
      setMessages(data.messages);
    }).catch(() => setMessages([]));
  }, [activeThreadId]);

  // Auto-scroll
  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Start new thread
  async function handleNewThread() {
    const t = await api.createThread();
    setThreads((prev) => [t, ...prev]);
    setActiveThreadId(t.id);
    setMessages([]);
  }

  // Send message
  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || streaming) return;

    let threadId = activeThreadId;
    if (!threadId) {
      const t = await api.createThread();
      setThreads((prev) => [t, ...prev]);
      threadId = t.id;
      setActiveThreadId(t.id);
    }

    const userMsg: MessageItem = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);
    setAgentStep("");

    try {
      const response = await api.streamChat(threadId, userMsg.content, mode);
      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";
      let assistantContent = "";
      const assistantId = crypto.randomUUID();

      setMessages((prev) => [...prev, {
        id: assistantId,
        role: "assistant",
        content: "",
        citations: [],
        created_at: new Date().toISOString(),
      }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            continue; // next line will be data
          }
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.content) {
                // token event
                assistantContent += data.content;
                setMessages((prev) => prev.map((m) =>
                  m.id === assistantId ? { ...m, content: assistantContent } : m
                ));
              }
              if (data.node) {
                // agent_step event
                setAgentStep(data.node);
              }
              if (data.route) {
                // done event
                setAgentStep("");
              }
            } catch {
              // skip malformed
            }
          }
        }
      }
    } catch (err) {
      console.error("Stream error:", err);
    } finally {
      setStreaming(false);
      setAgentStep("");
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Thread sidebar */}
      <aside className="w-60 border-r border-neutral-200 flex flex-col">
        <div className="p-3 border-b border-neutral-200">
          <button
            onClick={handleNewThread}
            className="w-full rounded bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            + 新建会话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {threads.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveThreadId(t.id)}
              className={`w-full text-left px-3 py-2 rounded text-sm truncate ${
                t.id === activeThreadId
                  ? "bg-blue-100 text-blue-800"
                  : "hover:bg-neutral-100"
              }`}
            >
              {t.title ?? "New conversation"}
              {t.is_stale && <span className="ml-1 text-amber-500">⚠</span>}
            </button>
          ))}
        </div>
      </aside>

      {/* Chat area */}
      <main className="flex-1 flex flex-col">
        {/* Mode toggle */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-neutral-200">
          <span className="text-xs text-neutral-500">模式:</span>
          {(["agent", "baseline"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1 rounded text-xs font-medium ${
                mode === m
                  ? "bg-blue-600 text-white"
                  : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
              }`}
            >
              {m === "agent" ? "Agent" : "Baseline"}
            </button>
          ))}
          {agentStep && (
            <span className="ml-auto text-xs text-blue-500 animate-pulse">
              {agentStep}...
            </span>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !activeThreadId && (
            <p className="text-center text-neutral-400 mt-20">
              选择一个会话或新建一个开始对话
            </p>
          )}
          {messages.length === 0 && activeThreadId && (
            <p className="text-center text-neutral-400 mt-20">
              发送消息开始对话
            </p>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-neutral-100 text-neutral-800"
                }`}
              >
                {msg.content || (msg.role === "assistant" && streaming ? "..." : "")}
                {msg.citations.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-neutral-300 text-xs text-neutral-500">
                    {msg.citations.map((c, i) => (
                      <div key={i}>📄 {c.source}: {c.text_preview.slice(0, 80)}...</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEnd} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="border-t border-neutral-200 p-4 flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={streaming ? "回复中…" : "输入问题…"}
            className="flex-1 rounded border border-neutral-300 px-4 py-2 text-sm"
            disabled={streaming}
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="rounded bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            发送
          </button>
        </form>
      </main>
    </div>
  );
}
