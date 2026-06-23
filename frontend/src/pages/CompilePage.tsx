import { Sparkles } from "lucide-react";
import { EmptyState } from "../components/common/EmptyState";

/** Placeholder for Phase 1. Prompt input, the staged pipeline, and result tabs land in Phase 2. */
export function CompilePage() {
  return (
    <EmptyState
      icon={Sparkles}
      title="Compile workspace"
      description="Prompt input and the live compiler pipeline arrive in Phase 2."
    />
  );
}
