import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as compilerApi from "../../frontend/src/api/compiler";
import { PROMPT_EXAMPLES } from "../../frontend/src/lib/promptExamples";
import { CompilePage } from "../../frontend/src/pages/CompilePage";
import { useCompileStore } from "../../frontend/src/store/compileStore";
import { MOCK_COMPILATION_RESULT } from "./fixtures/compilationResult";

vi.mock("../../frontend/src/api/compiler");

function resetStore() {
  useCompileStore.setState({ status: "idle", prompt: "", result: null, error: null, history: [] });
}

describe("CompilePage", () => {
  beforeEach(() => {
    resetStore();
    vi.restoreAllMocks();
  });

  it("populates the prompt editor when a prompt card is clicked", () => {
    render(<CompilePage />);
    fireEvent.click(screen.getByText("Todo Application"));
    const todoPrompt = PROMPT_EXAMPLES.find((example) => example.id === "todo")?.prompt;
    expect(screen.getByLabelText("System prompt")).toHaveValue(todoPrompt);
  });

  it("calls the compile API with the prompt and renders the pipeline and result tabs on success", async () => {
    const compileMock = vi.spyOn(compilerApi, "compile").mockResolvedValue(MOCK_COMPILATION_RESULT);
    render(<CompilePage />);

    fireEvent.change(screen.getByLabelText("System prompt"), { target: { value: "Build a CRM" } });
    fireEvent.click(screen.getByRole("button", { name: /compile/i }));

    await waitFor(() => expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument());
    expect(compileMock).toHaveBeenCalledWith("Build a CRM");
    expect(screen.getByText("Intent Extraction")).toBeInTheDocument();
  });

  it("shows an error banner with a working retry when compilation fails", async () => {
    const compileMock = vi
      .spyOn(compilerApi, "compile")
      .mockRejectedValueOnce({ kind: "network", message: "Could not reach the AI Compiler backend." })
      .mockResolvedValueOnce(MOCK_COMPILATION_RESULT);
    render(<CompilePage />);

    fireEvent.change(screen.getByLabelText("System prompt"), { target: { value: "Build a CRM" } });
    fireEvent.click(screen.getByRole("button", { name: /compile/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByText("Could not reach the AI Compiler backend.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument());
    expect(compileMock).toHaveBeenCalledTimes(2);
  });

  it("does not submit when the prompt is empty", () => {
    const compileMock = vi.spyOn(compilerApi, "compile");
    render(<CompilePage />);
    expect(screen.getByRole("button", { name: /compile/i })).toBeDisabled();
    expect(compileMock).not.toHaveBeenCalled();
  });
});
