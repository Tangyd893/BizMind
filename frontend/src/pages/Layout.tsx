import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-16 border-b border-neutral-200 flex items-center justify-between px-6">
        <div className="flex items-center gap-6">
          <Link to="/chat" className="text-lg font-semibold tracking-tight">
            BizMind
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link to="/chat" className="text-neutral-600 hover:text-neutral-900">
              对话
            </Link>
            <Link to="/documents" className="text-neutral-600 hover:text-neutral-900">
              文档
            </Link>
            <Link to="/eval" className="text-neutral-600 hover:text-neutral-900">
              评测
            </Link>
            {user?.role === "ADMIN" && (
              <Link to="/admin" className="text-neutral-600 hover:text-neutral-900">
                管理
              </Link>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {user && (
            <span className="text-neutral-500">
              {user.email} ({user.role})
            </span>
          )}
          <button
            onClick={handleLogout}
            className="text-neutral-400 hover:text-red-600"
          >
            退出
          </button>
        </div>
      </header>
      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
}
