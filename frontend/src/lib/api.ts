const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BACKEND_URL}/api${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "An error occurred";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      // Ignored
    }
    const error = new Error(errorDetail) as any;
    error.status = response.status;
    throw error;
  }

  return response.json();
}
