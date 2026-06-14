import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api/client";
import type { DocumentItem } from "../api/client";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  const loadDocs = useCallback(async () => {
    try {
      const data = await api.fetchDocuments(page, statusFilter || undefined);
      setDocs(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    }
  }, [page, statusFilter]);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadDocument(file);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.deleteDocument(id);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / 20));

  return (
    <div className="mx-auto max-w-4xl space-y-6 py-8 px-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">文档管理</h1>
        <label className="cursor-pointer rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          {uploading ? "上传中…" : "+ 上传文档"}
          <input
            ref={fileInput}
            type="file"
            accept=".md,.txt,.pdf"
            onChange={handleUpload}
            className="hidden"
            disabled={uploading}
          />
        </label>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {["", "pending", "indexing", "indexed", "failed"].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`px-3 py-1 rounded text-xs font-medium ${
              statusFilter === s
                ? "bg-blue-600 text-white"
                : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
            }`}
          >
            {s || "全部"}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left">
            <tr>
              <th className="px-4 py-2 font-medium">文件名</th>
              <th className="px-4 py-2 font-medium">类型</th>
              <th className="px-4 py-2 font-medium">状态</th>
              <th className="px-4 py-2 font-medium">块数</th>
              <th className="px-4 py-2 font-medium">上传时间</th>
              <th className="px-4 py-2 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {docs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-neutral-400">
                  暂无文档，请上传
                </td>
              </tr>
            )}
            {docs.map((doc) => (
              <tr key={doc.id} className="border-t border-neutral-100">
                <td className="px-4 py-2 truncate max-w-48">{doc.filename}</td>
                <td className="px-4 py-2 text-neutral-500">{doc.mime_type}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={doc.status} />
                </td>
                <td className="px-4 py-2">{doc.chunk_count}</td>
                <td className="px-4 py-2 text-neutral-500">
                  {new Date(doc.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-2">
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-red-500 hover:underline text-xs"
                  >
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1 text-sm rounded border border-neutral-300 disabled:opacity-30"
          >
            上一页
          </button>
          <span className="px-3 py-1 text-sm text-neutral-500">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1 text-sm rounded border border-neutral-300 disabled:opacity-30"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    indexing: "bg-blue-100 text-blue-800",
    indexed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] ?? "bg-neutral-100"}`}>
      {status}
    </span>
  );
}
