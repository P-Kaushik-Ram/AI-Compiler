/** Thin fetch wrapper shared by every API module; normalizes failures via errors.ts. */
import { httpError, networkError } from "./errors";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function apiPost<TResponse>(path: string, body: unknown): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw networkError();
  }

  if (!response.ok) {
    throw await httpError(response);
  }

  return response.json() as Promise<TResponse>;
}
