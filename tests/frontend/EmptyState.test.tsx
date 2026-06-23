import { render, screen } from "@testing-library/react";
import { Sparkles } from "lucide-react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "../../frontend/src/components/common/EmptyState";

describe("EmptyState", () => {
  it("renders the title, description, and an optional action", () => {
    render(
      <EmptyState
        icon={Sparkles}
        title="Compile workspace"
        description="Coming soon."
        action={<button>Go</button>}
      />
    );
    expect(screen.getByText("Compile workspace")).toBeInTheDocument();
    expect(screen.getByText("Coming soon.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go" })).toBeInTheDocument();
  });

  it("renders without a description or action", () => {
    render(<EmptyState icon={Sparkles} title="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });
});
