import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Loading } from "../../frontend/src/components/common/Loading";

describe("Loading", () => {
  it("renders an optional label", () => {
    render(<Loading label="Compiling..." />);
    expect(screen.getByText("Compiling...")).toBeInTheDocument();
  });

  it("renders without a label", () => {
    const { container } = render(<Loading />);
    expect(container.querySelector(".spin")).toBeInTheDocument();
  });
});
