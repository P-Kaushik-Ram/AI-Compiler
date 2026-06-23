import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "../../frontend/src/components/common/Badge";

describe("Badge", () => {
  it("renders its label text", () => {
    render(<Badge variant="brand">v1.0</Badge>);
    expect(screen.getByText("v1.0")).toBeInTheDocument();
  });

  it("defaults to the neutral variant without throwing", () => {
    render(<Badge>neutral</Badge>);
    expect(screen.getByText("neutral")).toBeInTheDocument();
  });
});
