import { useCallback, useEffect, useState } from "react";
import * as api from "../api/client";

interface EvalRun {
  id: string;
  mode: string;
  dataset_path: string;
  sample_count: number;
  metrics: Record<string, number>;
  duration_sec?: number | null;
  created_at: string;
}

export default function EvalPage() {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [running, setRunning] = useState(false);
  const [mode, setMode] = useState<"baseline" | "agent" | "both">("baseline");
  const [error, setError] = useState("");

  const loadRuns = useCallback(async () => {
    try {
      const token = localStorage.getItem("bizmind_token");
      const resp = await fetch(`${api.API_BASE}/eval/results`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!resp.ok) throw new Error("Failed to load");
      const data = await resp.json();
      setRuns(data.items ?? []);
    } catch {
      // admin only
    }
  }, []);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  async function handleRun() {
    setRunning(true);
    setError("");
    try {
      const token = localStorage.getItem("bizmind_token");
      const resp = await fetch(`${api.API_BASE}/eval/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ mode, dataset: "default" }),
      });
      if (!resp.ok) {
        const body = await resp.json();
        throw new Error(body?.error?.message ?? "Eval failed");
      }
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 py-8 px-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">RAGAS 评测</h1>
        <div className="flex gap-3 items-center">
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as typeof mode)}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm"
          >
            <option value="baseline">Baseline RAG</option>
            <option value="agent">Agentic RAG</option>
            <option value="both">Both (对比)</option>
          </select>
          <button
            onClick={handleRun}
            disabled={running}
            className="rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {running ? "运行中…" : "▶ 运行评测"}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {runs.length === 0 ? (
        <p className="text-center text-neutral-400 py-12">
          暂无评测记录。点击「运行评测」基于 Golden QA 数据集进行评估。
        </p>
      ) : (
        <div className="space-y-4">
          {runs.map((run) => (
            <div
              key={run.id}
              className="rounded-lg border border-neutral-200 p-4 space-y-3"
            >
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">
                  {run.mode === "both" ? "Baseline vs Agent" : run.mode.toUpperCase()}
                </span>
                <span className="text-neutral-500">
                  {run.sample_count} 条 · {run.duration_sec}s · {new Date(run.created_at).toLocaleString()}
                </span>
              </div>
              <MetricsTable metrics={run.metrics} mode={run.mode} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetricsTable({ metrics, mode }: { metrics: Record<string, number | Record<string, number>>, mode: string }) {
  if (mode === "both" && typeof metrics.baseline === "object" && typeof metrics.agent === "object") {
    return (
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-neutral-500">
            <th className="py-1 pr-4">指标</th>
            <th className="py-1 pr-4">Baseline</th>
            <th className="py-1">Agent</th>
          </tr>
        </thead>
        <tbody>
          {(["faithfulness", "answer_relevancy", "context_precision", "context_recall"] as const).map((key) => (
            <tr key={key} className="border-t border-neutral-100">
              <td className="py-1.5 font-medium">{key}</td>
              <td className="py-1.5">{(metrics.baseline as Record<string, number>)[key]?.toFixed(4) ?? "-"}</td>
              <td className="py-1.5">{(metrics.agent as Record<string, number>)[key]?.toFixed(4) ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <div className="flex gap-6 text-sm">
      {Object.entries(metrics).filter(([k]) => k !== "error").map(([key, value]) => (
        <div key={key}>
          <span className="text-neutral-500">{key}: </span>
          <span className="font-medium">{(value as number).toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
}
