import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultTabs } from "../../frontend/src/components/compile/ResultTabs";
import { MOCK_COMPILATION_RESULT } from "./fixtures/compilationResult";

describe("ResultTabs", () => {
  it("renders the tabs in the required order, with Raw JSON last", () => {
    render(<ResultTabs result={MOCK_COMPILATION_RESULT} />);
    const tabs = screen.getAllByRole("tab").map((tab) => tab.textContent);
    expect(tabs).toEqual(["Overview", "Intent", "System Design", "Schema", "Validation", "Raw JSON"]);
  });

  it("shows the Overview tab by default with the compilation decision", () => {
    render(<ResultTabs result={MOCK_COMPILATION_RESULT} />);
    expect(screen.getByText("Compilation Decision")).toBeInTheDocument();
    expect(screen.getByText("Proceed")).toBeInTheDocument();
  });

  it("switches to the Intent tab and shows the extracted entity", () => {
    render(<ResultTabs result={MOCK_COMPILATION_RESULT} />);
    fireEvent.click(screen.getByRole("tab", { name: "Intent" }));
    expect(screen.getByText("A task item owned by a user")).toBeInTheDocument();
  });

  it("switches to the Raw JSON tab and shows the serialized result", () => {
    render(<ResultTabs result={MOCK_COMPILATION_RESULT} />);
    fireEvent.click(screen.getByRole("tab", { name: "Raw JSON" }));
    expect(screen.getByText(/"compilation_id"/)).toBeInTheDocument();
  });

  it("shows an empty-state on the Validation tab when the report is missing", () => {
    render(<ResultTabs result={{ ...MOCK_COMPILATION_RESULT, validation_report: null }} />);
    fireEvent.click(screen.getByRole("tab", { name: "Validation" }));
    expect(screen.getByText("Validation stage not reached")).toBeInTheDocument();
  });

  it("highlights the active tab", () => {
    render(<ResultTabs result={MOCK_COMPILATION_RESULT} />);
    const intentTab = screen.getByRole("tab", { name: "Intent" });
    fireEvent.click(intentTab);
    expect(within(screen.getByRole("tablist")).getByRole("tab", { name: "Intent" })).toHaveAttribute(
      "aria-selected",
      "true"
    );
  });
});
