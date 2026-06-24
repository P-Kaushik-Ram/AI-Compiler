import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AppRoutes } from "../../frontend/src/router";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>
  );
}

describe("AppRoutes", () => {
  it("renders the top nav brand, version, and test-status badges on every route", () => {
    renderAt("/");
    expect(screen.getByText("AI Compiler")).toBeInTheDocument();
    expect(screen.getByText("v1.0")).toBeInTheDocument();
    expect(screen.getByText("102 Tests Passing")).toBeInTheDocument();
  });

  it("renders the Compile page at /", () => {
    renderAt("/");
    expect(screen.getByText("Compile a system from a prompt")).toBeInTheDocument();
  });

  it("renders the Evaluation page at /evaluate", () => {
    renderAt("/evaluate");
    expect(screen.getByText("Evaluation dashboard")).toBeInTheDocument();
  });

  it("renders the not-found page for an unknown route", () => {
    renderAt("/does-not-exist");
    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });
});
