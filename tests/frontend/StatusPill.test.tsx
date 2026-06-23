import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusPill } from "../../frontend/src/components/common/StatusPill";

describe("StatusPill", () => {
  it("renders its label", () => {
    render(<StatusPill label="102 Tests Passing" status="success" />);
    expect(screen.getByText("102 Tests Passing")).toBeInTheDocument();
  });
});
