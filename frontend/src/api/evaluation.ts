import { apiPost } from "./client";
import type { BenchmarkResult, DatasetCase } from "../types/evaluation";

/** Calls POST /evaluate. Not yet wired into any page — a later phase owns the Evaluation dashboard. */
export function evaluate(datasetName: string, cases: DatasetCase[]): Promise<BenchmarkResult> {
  return apiPost<BenchmarkResult>("/evaluate", { dataset_name: datasetName, cases });
}
