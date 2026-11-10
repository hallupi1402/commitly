export class ApiError extends Error {
  constructor(public status: number, public payload: any) {
    super(payload?.message || `Request failed (${status})`);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<{ data: T; etag: string | null }> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { ...(init.body ? { "Content-Type": "application/json" } : {}), ...init.headers },
  });
  const body = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, body);
  return { data: body as T, etag: response.headers.get("ETag") };
}

export function jsonBody(value: unknown): string {
  return JSON.stringify(value);
}
