import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ErrorBanner } from "../../frontend/src/components/common/ErrorBanner";

describe("ErrorBanner", () => {
  it("renders the message and detail", () => {
    render(<ErrorBanner message="Request failed" detail="Status 500" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Request failed")).toBeInTheDocument();
    expect(screen.getByText("Status 500")).toBeInTheDocument();
  });

  it("calls onRetry when the retry button is clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Request failed" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("omits the retry button when no handler is given", () => {
    render(<ErrorBanner message="Request failed" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
