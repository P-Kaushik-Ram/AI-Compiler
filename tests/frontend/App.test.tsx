import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "../../frontend/src/App";

describe("App", () => {
  it("renders the heading", () => {
    render(<App />);
    expect(screen.getByText("AI Compiler")).toBeInTheDocument();
  });
});
