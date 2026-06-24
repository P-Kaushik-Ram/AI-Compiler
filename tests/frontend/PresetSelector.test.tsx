import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PresetSelector } from "../../frontend/src/components/evaluation/PresetSelector";

describe("PresetSelector", () => {
  it("renders all four preset options", () => {
    render(<PresetSelector value="crm" onChange={vi.fn()} />);
    expect(screen.getByText("CRM Benchmark")).toBeInTheDocument();
    expect(screen.getByText("Mixed Domains")).toBeInTheDocument();
    expect(screen.getByText("Healthcare Benchmark")).toBeInTheDocument();
    expect(screen.getByText("Custom Dataset")).toBeInTheDocument();
  });

  it("marks the active preset as pressed", () => {
    render(<PresetSelector value="healthcare" onChange={vi.fn()} />);
    expect(screen.getByText("Healthcare Benchmark").closest("button")).toHaveAttribute(
      "aria-pressed",
      "true"
    );
    expect(screen.getByText("CRM Benchmark").closest("button")).toHaveAttribute("aria-pressed", "false");
  });

  it("calls onChange with the clicked preset id", () => {
    const onChange = vi.fn();
    render(<PresetSelector value="crm" onChange={onChange} />);
    fireEvent.click(screen.getByText("Custom Dataset"));
    expect(onChange).toHaveBeenCalledWith("custom");
  });

  it("disables every option when disabled is true", () => {
    render(<PresetSelector value="crm" onChange={vi.fn()} disabled />);
    expect(screen.getByText("Mixed Domains").closest("button")).toBeDisabled();
  });
});
