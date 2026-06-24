import { create } from "zustand";
import type { AppError } from "../api/errors";
import type { BenchmarkResult } from "../types/evaluation";

export type BenchmarkPreset = "crm" | "mixed" | "healthcare" | "custom";
export type EvaluationStatus = "idle" | "loading" | "success" | "error";

interface EvaluationState {
  preset: BenchmarkPreset;
  /** Raw textarea contents (one prompt per line) backing the "custom" preset. */
  customInput: string;
  status: EvaluationStatus;
  result: BenchmarkResult | null;
  error: AppError | null;
  setPreset: (preset: BenchmarkPreset) => void;
  setCustomInput: (value: string) => void;
  start: () => void;
  succeed: (result: BenchmarkResult) => void;
  fail: (error: AppError) => void;
  reset: () => void;
}

export const useEvaluationStore = create<EvaluationState>((set) => ({
  preset: "crm",
  customInput: "",
  status: "idle",
  result: null,
  error: null,
  setPreset: (preset) => set({ preset }),
  setCustomInput: (customInput) => set({ customInput }),
  start: () => set({ status: "loading", error: null }),
  succeed: (result) => set({ status: "success", result }),
  fail: (error) => set({ status: "error", error }),
  reset: () => set({ status: "idle", result: null, error: null }),
}));
