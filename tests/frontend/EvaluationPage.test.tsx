import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as evaluationApi from "../../frontend/src/api/evaluation";
import { EvaluationPage } from "../../frontend/src/pages/EvaluationPage";
import { useEvaluationStore } from "../../frontend/src/store/evaluationStore";
import { MOCK_BENCHMARK_RESULT } from "./fixtures/benchmarkResult";

vi.mock("../../frontend/src/api/evaluation");

function resetStore() {
  useEvaluationStore.setState({ preset: "crm", customInput: "", status: "idle", result: null, error: null });
}

describe("EvaluationPage", () => {
  beforeEach(() => {
    resetStore();
    vi.restoreAllMocks();
  });

  it("shows the idle empty state before any run", () => {
    render(<EvaluationPage />);
    expect(screen.getByText("No evaluation run yet")).toBeInTheDocument();
  });

  it("defaults to the CRM preset with its 4 cases ready to run", () => {
    render(<EvaluationPage />);
    expect(screen.getByText("CRM Benchmark").closest("button")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("4 cases ready")).toBeInTheDocument();
  });

  it("runs the CRM preset and renders the benchmark summary on success", async () => {
    const evaluateMock = vi.spyOn(evaluationApi, "evaluate").mockResolvedValue(MOCK_BENCHMARK_RESULT);
    render(<EvaluationPage />);

    fireEvent.click(screen.getByRole("button", { name: /run evaluation/i }));

    await waitFor(() => expect(screen.getByText("crm-preset")).toBeInTheDocument());
    expect(evaluateMock).toHaveBeenCalledWith("crm-preset", expect.arrayContaining([expect.objectContaining({ case_id: "crm-1" })]));
    expect(screen.getByText("Stage Metrics")).toBeInTheDocument();
  });

  it("switches to the custom preset, disables Run until text is entered, then runs it", async () => {
    const evaluateMock = vi.spyOn(evaluationApi, "evaluate").mockResolvedValue(MOCK_BENCHMARK_RESULT);
    render(<EvaluationPage />);

    fireEvent.click(screen.getByText("Custom Dataset"));
    expect(screen.getByRole("button", { name: /run evaluation/i })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Enter one prompt per line"), {
      target: { value: "Build a CRM\nBuild a todo app" },
    });
    expect(screen.getByRole("button", { name: /run evaluation/i })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: /run evaluation/i }));
    await waitFor(() => expect(screen.getByText("crm-preset")).toBeInTheDocument());
    expect(evaluateMock).toHaveBeenCalledWith(
      "custom-dataset",
      expect.arrayContaining([expect.objectContaining({ prompt: "Build a CRM" })])
    );
  });

  it("shows an error banner with a working retry when evaluation fails", async () => {
    const evaluateMock = vi
      .spyOn(evaluationApi, "evaluate")
      .mockRejectedValueOnce({ kind: "network", message: "Could not reach the AI Compiler backend." })
      .mockResolvedValueOnce(MOCK_BENCHMARK_RESULT);
    render(<EvaluationPage />);

    fireEvent.click(screen.getByRole("button", { name: /run evaluation/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByText("Could not reach the AI Compiler backend.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByText("crm-preset")).toBeInTheDocument());
    expect(evaluateMock).toHaveBeenCalledTimes(2);
  });
});
