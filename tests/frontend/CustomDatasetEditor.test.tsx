import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CustomDatasetEditor } from "../../frontend/src/components/evaluation/CustomDatasetEditor";

describe("CustomDatasetEditor", () => {
  it("shows a singular case count for one non-blank line", () => {
    render(<CustomDatasetEditor value="Build a CRM" onChange={vi.fn()} />);
    expect(screen.getByText("1 case")).toBeInTheDocument();
  });

  it("counts only non-blank lines", () => {
    render(<CustomDatasetEditor value={"Build a CRM\n\nBuild a todo app\n   \n"} onChange={vi.fn()} />);
    expect(screen.getByText("2 cases")).toBeInTheDocument();
  });

  it("shows zero cases for empty input", () => {
    render(<CustomDatasetEditor value="" onChange={vi.fn()} />);
    expect(screen.getByText("0 cases")).toBeInTheDocument();
  });

  it("calls onChange as the user types", () => {
    const onChange = vi.fn();
    render(<CustomDatasetEditor value="" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Enter one prompt per line"), {
      target: { value: "Build a todo app" },
    });
    expect(onChange).toHaveBeenCalledWith("Build a todo app");
  });

  it("disables the textarea when disabled is true", () => {
    render(<CustomDatasetEditor value="" onChange={vi.fn()} disabled />);
    expect(screen.getByLabelText("Enter one prompt per line")).toBeDisabled();
  });
});
