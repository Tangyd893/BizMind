import { useEffect, useState } from "react";
import * as api from "../api/client";
import type { AdminUser } from "../api/client";

export default function AdminPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadUsers(p: number) {
    setLoading(true);
    setError("");
    try {
      const data = await api.fetchAdminUsers(p);
      setUsers(data.items);
      setTotal(data.total);
      setPage(data.page);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers(1);
  }, []);

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-semibold mb-4">用户管理</h1>

      {error && (
        <div className="mb-4 rounded bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-neutral-400">加载中…</p>
      ) : (
        <>
          <div className="mb-2 text-sm text-neutral-500">
            共 {total} 位用户
          </div>
          <div className="overflow-x-auto rounded border border-neutral-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200 bg-neutral-50 text-left">
                  <th className="px-4 py-2 font-medium">邮箱</th>
                  <th className="px-4 py-2 font-medium">角色</th>
                  <th className="px-4 py-2 font-medium">租户 ID</th>
                  <th className="px-4 py-2 font-medium">注册时间</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-neutral-400">
                      暂无用户
                    </td>
                  </tr>
                )}
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                    <td className="px-4 py-2">{u.email}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`rounded px-2 py-0.5 text-xs font-medium ${
                          u.role === "ADMIN"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-neutral-100 text-neutral-600"
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-neutral-400">
                      {u.tenant_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-2 text-neutral-500">
                      {new Date(u.created_at).toLocaleString("zh-CN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <button
                onClick={() => loadUsers(page - 1)}
                disabled={page <= 1}
                className="rounded border border-neutral-300 px-3 py-1 text-sm hover:bg-neutral-100 disabled:opacity-40"
              >
                上一页
              </button>
              <span className="text-sm text-neutral-500">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => loadUsers(page + 1)}
                disabled={page >= totalPages}
                className="rounded border border-neutral-300 px-3 py-1 text-sm hover:bg-neutral-100 disabled:opacity-40"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
