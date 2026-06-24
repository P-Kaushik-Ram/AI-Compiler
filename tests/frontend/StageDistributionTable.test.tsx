import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StageDistributionTable } from "../../frontend/src/components/evaluation/StageDistributionTable";
import { MOCK_BENCHMARK_RESULT } from "./fixtures/benchmarkResult";

describe("StageDistributionTable", () => {
  it("renders a row for every known stage in both tables", () => {
    render(<StageDistributionTable result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("Confidence by Stage")).toBeInTheDocument();
    expect(screen.getByText("Duration by Stage")).toBeInTheDocument();
    expect(screen.getAllByText("intent extraction")).toHaveLength(2);
    expect(screen.getAllByText("validation")).toHaveLength(2);
  });

  it("formats confidence and duration distributions using their respective formatters", () => {
    render(<StageDistributionTable result={MOCK_BENCHMARK_RESULT} />);
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("2.1 ms")).toBeInTheDocument();
  });

  it("shows an empty message when a distribution map is empty", () => {
    render(
      <StageDistributionTable
        result={{ ...MOCK_BENCHMARK_RESULT, confidence_by_stage: {}, duration_by_stage_ms: {} }}
      />
    );
    expect(screen.getAllByText("No data recorded.")).toHaveLength(2);
  });
});
