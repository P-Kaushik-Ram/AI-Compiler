import { Skeleton } from "../common/Skeleton";

const METRIC_CARD_COUNT = 5;

/** Shown in place of the benchmark results while an evaluation run is in flight. */
export function EvaluationSkeleton() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "var(--space-4)",
        }}
      >
        {Array.from({ length: METRIC_CARD_COUNT }).map((_, index) => (
          <Skeleton key={index} height={72} />
        ))}
      </div>
      <Skeleton height={180} />
      <Skeleton height={100} />
    </div>
  );
}
