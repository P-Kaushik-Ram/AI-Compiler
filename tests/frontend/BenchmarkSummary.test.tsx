import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BenchmarkSummary } from "../../frontend/src/components/evaluation/BenchmarkSummary";
import { MOCK_BENCHMARK_RESULT } from "./fixtures/benchmarkResult";

describe("BenchmarkSummary", () => {
  it("renders the dataset name, status, and case count", () => {
    render(<BenchmarkSummary result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("crm-preset")).toBeInTheDocument();
    expect(screen.getByText("complete")).toBeInTheDocument();
    expect(screen.getByText("4 cases")).toBeInTheDocument();
  });

  it("formats every rate as a rounded percentage", () => {
    render(<BenchmarkSummary result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("formats the total duration", () => {
    render(<BenchmarkSummary result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("42.5 ms")).toBeInTheDocument();
  });
});
