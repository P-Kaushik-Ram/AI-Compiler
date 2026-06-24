import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PromptCards } from "../../frontend/src/components/compile/PromptCards";
import { PROMPT_EXAMPLES } from "../../frontend/src/lib/promptExamples";

describe("PromptCards", () => {
  it("renders one card per prompt example", () => {
    render(<PromptCards onSelect={vi.fn()} />);
    for (const example of PROMPT_EXAMPLES) {
      expect(screen.getByText(example.title)).toBeInTheDocument();
    }
  });

  it("calls onSelect with the example's full prompt when a card is clicked", () => {
    const onSelect = vi.fn();
    render(<PromptCards onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Todo Application"));
    expect(onSelect).toHaveBeenCalledWith(PROMPT_EXAMPLES.find((example) => example.id === "todo")?.prompt);
  });

  it("disables every card when disabled is true", () => {
    render(<PromptCards onSelect={vi.fn()} disabled />);
    for (const example of PROMPT_EXAMPLES) {
      expect(screen.getByText(example.title).closest("button")).toBeDisabled();
    }
  });
});
