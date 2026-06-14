import { useHealth } from "./hooks/useHealth";

export default function App() {
  const { data, isLoading, isError } = useHealth();

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 p-8">
      <h1 className="text-3xl font-semibold tracking-tight">BizMind</h1>
      <p className="text-neutral-600">企业知识智能助手 — 脚手架已就绪，P1 开发进行中。</p>
      <section className="rounded-lg border border-neutral-200 p-4">
        <h2 className="mb-2 text-sm font-medium text-neutral-500">API 状态</h2>
        {isLoading && <p>检查中…</p>}
        {isError && <p className="text-red-600">无法连接后端，请先启动 API（端口 8000）。</p>}
        {data && (
          <p>
            状态：<strong>{data.status}</strong> · 版本 {data.version}
          </p>
        )}
      </section>
    </main>
  );
}
