import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PromptEditor } from "../../frontend/src/components/compile/PromptEditor";

describe("PromptEditor", () => {
  it("shows the live character count", () => {
    render(<PromptEditor value="Build a CRM" onChange={vi.fn()} onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByText("11 / 4,000 characters")).toBeInTheDocument();
  });

  it("disables the Compile button when the prompt is empty", () => {
    render(<PromptEditor value="" onChange={vi.fn()} onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByRole("button", { name: /compile/i })).toBeDisabled();
  });

  it("enables the Compile button once there is non-whitespace text", () => {
    render(<PromptEditor value="Build a CRM" onChange={vi.fn()} onSubmit={vi.fn()} isLoading={false} />);
    expect(screen.getByRole("button", { name: /compile/i })).toBeEnabled();
  });

  it("calls onSubmit when the Compile button is clicked", () => {
    const onSubmit = vi.fn();
    render(<PromptEditor value="Build a CRM" onChange={vi.fn()} onSubmit={onSubmit} isLoading={false} />);
    fireEvent.click(screen.getByRole("button", { name: /compile/i }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("shows a loading state and disables the textarea while compiling", () => {
    render(<PromptEditor value="Build a CRM" onChange={vi.fn()} onSubmit={vi.fn()} isLoading />);
    expect(screen.getByRole("button", { name: /compiling/i })).toBeDisabled();
    expect(screen.getByLabelText("System prompt")).toBeDisabled();
  });

  it("calls onChange as the user types", () => {
    const onChange = vi.fn();
    render(<PromptEditor value="" onChange={onChange} onSubmit={vi.fn()} isLoading={false} />);
    fireEvent.change(screen.getByLabelText("System prompt"), { target: { value: "Build a todo app" } });
    expect(onChange).toHaveBeenCalledWith("Build a todo app");
  });
});
