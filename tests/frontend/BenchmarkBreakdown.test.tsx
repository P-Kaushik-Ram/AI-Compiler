import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BenchmarkBreakdown } from "../../frontend/src/components/evaluation/BenchmarkBreakdown";
import { MOCK_BENCHMARK_RESULT } from "./fixtures/benchmarkResult";

describe("BenchmarkBreakdown", () => {
  it("renders dataset category counts", () => {
    render(<BenchmarkBreakdown result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("crm: 4")).toBeInTheDocument();
  });

  it("renders only non-zero failure categories", () => {
    render(<BenchmarkBreakdown result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("intent ambiguous: 1")).toBeInTheDocument();
    expect(screen.queryByText(/design inconsistent/)).not.toBeInTheDocument();
  });

  it("renders only non-zero validation finding severities", () => {
    render(<BenchmarkBreakdown result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("critical: 3")).toBeInTheDocument();
    expect(screen.queryByText(/^info:/)).not.toBeInTheDocument();
  });

  it("hides the Dataset Errors section when there are none", () => {
    render(<BenchmarkBreakdown result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.queryByText("Dataset Errors")).not.toBeInTheDocument();
  });

  it("renders dataset errors when present", () => {
    render(
      <BenchmarkBreakdown
        result={{
          ...MOCK_BENCHMARK_RESULT,
          dataset_errors: [{ case_id: "bad-1", raw_line_number: 3, error: "Invalid JSON." }],
        }}
      />
    );
    expect(screen.getByRole("heading", { level: 3, name: /Dataset Errors/ })).toHaveTextContent(
      "Dataset Errors(1)"
    );
    expect(screen.getByText("Invalid JSON.")).toBeInTheDocument();
  });
});
