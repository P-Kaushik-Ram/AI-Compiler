import { CompassIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { EmptyState } from "../components/common/EmptyState";

export function NotFoundPage() {
  return (
    <EmptyState
      icon={CompassIcon}
      title="Page not found"
      description="The page you're looking for doesn't exist."
      action={
        <Link
          to="/"
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: "var(--color-brand)",
            textDecoration: "none",
          }}
        >
          Back to Compile
        </Link>
      }
    />
  );
}
