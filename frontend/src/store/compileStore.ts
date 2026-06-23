import { create } from "zustand";
import type { AppError } from "../api/errors";
import type { CompilationResult } from "../types/runtime";

export type CompileStatus = "idle" | "loading" | "success" | "error";

interface CompileState {
  status: CompileStatus;
  prompt: string;
  result: CompilationResult | null;
  error: AppError | null;
  /** In-session only — the backend has no persistence endpoint, so history is lost on refresh. */
  history: CompilationResult[];
  setPrompt: (prompt: string) => void;
  start: () => void;
  succeed: (result: CompilationResult) => void;
  fail: (error: AppError) => void;
  reset: () => void;
}

export const useCompileStore = create<CompileState>((set) => ({
  status: "idle",
  prompt: "",
  result: null,
  error: null,
  history: [],
  setPrompt: (prompt) => set({ prompt }),
  start: () => set({ status: "loading", error: null }),
  succeed: (result) =>
    set((state) => ({ status: "success", result, history: [result, ...state.history] })),
  fail: (error) => set({ status: "error", error }),
  reset: () => set({ status: "idle", result: null, error: null }),
}));
