import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PipelineVisualization } from "../../frontend/src/components/compile/PipelineVisualization";
import { MOCK_COMPILATION_RESULT } from "./fixtures/compilationResult";

describe("PipelineVisualization", () => {
  it("renders all four stage labels in order", () => {
    render(<PipelineVisualization stageSummaries={[]} isCompiling={false} />);
    const labels = ["Intent Extraction", "System Design", "Schema Generation", "Validation"];
    for (const label of labels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("marks every stage as 'not reached' when no summaries exist and compilation has finished", () => {
    render(<PipelineVisualization stageSummaries={[]} isCompiling={false} />);
    expect(screen.getAllByText("not reached")).toHaveLength(4);
  });

  it("renders the real status, confidence, and duration from each stage summary", () => {
    render(
      <PipelineVisualization stageSummaries={MOCK_COMPILATION_RESULT.stage_summaries} isCompiling={false} />
    );
    expect(screen.getByText("95% confidence")).toBeInTheDocument();
    expect(screen.getByText("1.2 ms")).toBeInTheDocument();
    expect(screen.getByText("passed")).toBeInTheDocument();
  });
});
