import { apiPost } from "./client";
import type { CompilationResult } from "../types/runtime";

/** Calls POST /compile. Not yet wired into any page — Phase 2 owns the Compile page logic. */
export function compile(prompt: string): Promise<CompilationResult> {
  return apiPost<CompilationResult>("/compile", { prompt });
}
