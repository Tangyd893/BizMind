const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export { API_BASE };
