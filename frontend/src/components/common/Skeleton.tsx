import type { CSSProperties } from "react";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  style?: CSSProperties;
}

/** A shimmering placeholder block shown while content is still loading. */
export function Skeleton({ width = "100%", height = 16, style }: SkeletonProps) {
  return (
    <div
      className="skeleton"
      style={{
        width,
        height,
        borderRadius: "var(--radius-sm)",
        ...style,
      }}
    />
  );
}
