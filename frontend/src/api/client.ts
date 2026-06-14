const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("bizmind_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body?.error?.message ?? response.statusText;
    throw new Error(message);
  }
  return response.json();
}

// Health
export async function fetchHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}

// Auth
export interface AuthResponse {
  user: { id: string; email: string; role: string; tenant_id: string; created_at: string };
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function register(email: string, password: string, tenant_name?: string) {
  return request<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, tenant_name }),
  });
}

export async function login(email: string, password: string) {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface UserInfo {
  id: string;
  email: string;
  role: string;
  tenant_id: string;
  created_at: string;
}

export async function fetchMe() {
  return request<UserInfo>("/auth/me");
}

// Documents
export interface DocumentItem {
  id: string;
  filename: string;
  mime_type: string;
  status: string;
  chunk_count: number;
  documents_version: number;
  error_message?: string | null;
  created_at: string;
  indexed_at?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export async function fetchDocuments(page = 1, status?: string) {
  const params = new URLSearchParams({ page: String(page), page_size: "20" });
  if (status) params.set("status", status);
  return request<PaginatedResponse<DocumentItem>>(`/documents?${params}`);
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const token = localStorage.getItem("bizmind_token");
  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? response.statusText);
  }
  return response.json() as Promise<DocumentItem>;
}

export async function deleteDocument(id: string) {
  await fetch(`${API_BASE}/documents/${id}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

// Threads
export interface ThreadItem {
  id: string;
  title?: string | null;
  documents_version: number;
  is_stale: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchThreads(page = 1) {
  const params = new URLSearchParams({ page: String(page), page_size: "20" });
  return request<PaginatedResponse<ThreadItem>>(`/threads?${params}`);
}

export async function createThread(title?: string) {
  return request<ThreadItem>("/threads", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export interface MessageItem {
  id: string;
  role: string;
  content: string;
  citations: Array<{ document_id: string; chunk_id: string; source: string; page?: number; text_preview: string }>;
  token_usage?: Record<string, number> | null;
  latency_ms?: number | null;
  created_at: string;
}

export interface ThreadMessagesResponse {
  thread_id: string;
  is_stale: boolean;
  documents_version: number;
  messages: MessageItem[];
}

export async function fetchMessages(threadId: string) {
  return request<ThreadMessagesResponse>(`/threads/${threadId}/messages`);
}

// Chat SSE
export function streamChat(threadId: string, message: string, mode: "baseline" | "agent" = "agent") {
  const token = localStorage.getItem("bizmind_token");
  return fetch(`${API_BASE}/chat/${mode}/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ thread_id: threadId, message }),
  });
}

export { API_BASE };
