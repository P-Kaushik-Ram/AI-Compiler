/** Normalizes fetch/network failures and FastAPI error bodies into one shape the UI can render. */

export type AppErrorKind = "network" | "validation" | "server" | "unknown";

export interface AppError {
  kind: AppErrorKind;
  message: string;
  detail?: string;
}

export function networkError(): AppError {
  return {
    kind: "network",
    message: "Could not reach the AI Compiler backend. Check that the API is running.",
  };
}

export async function httpError(response: Response): Promise<AppError> {
  const kind: AppErrorKind =
    response.status === 422 ? "validation" : response.status >= 500 ? "server" : "unknown";

  let detail: string | undefined;
  try {
    const body = await response.json();
    detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body?.detail ?? body);
  } catch {
    detail = undefined;
  }

  const message =
    kind === "validation"
      ? "The request was rejected as invalid."
      : `Request failed with status ${response.status}.`;

  return { kind, message, detail };
}
