import { Skeleton } from "../common/Skeleton";

const TAB_COUNT = 6;

/** Shown in place of ResultTabs while a compilation is in flight and no result exists yet. */
export function ResultsSkeleton() {
  return (
    <div>
      <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-5)" }}>
        {Array.from({ length: TAB_COUNT }).map((_, index) => (
          <Skeleton key={index} width={index === 0 ? 84 : 96} height={28} />
        ))}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
        <Skeleton height={72} />
        <Skeleton height={72} />
        <Skeleton height={140} />
      </div>
    </div>
  );
}
