import { useState } from "react";
import type { CompilationResult } from "../../types/runtime";
import { IntentTab } from "./tabs/IntentTab";
import { OverviewTab } from "./tabs/OverviewTab";
import { RawJsonTab } from "./tabs/RawJsonTab";
import { SchemaTab } from "./tabs/SchemaTab";
import { SystemDesignTab } from "./tabs/SystemDesignTab";
import { ValidationTab } from "./tabs/ValidationTab";

/** Raw JSON must always be the final tab. */
const TAB_NAMES = ["Overview", "Intent", "System Design", "Schema", "Validation", "Raw JSON"] as const;
type TabName = (typeof TAB_NAMES)[number];

interface ResultTabsProps {
  result: CompilationResult;
}

export function ResultTabs({ result }: ResultTabsProps) {
  const [activeTab, setActiveTab] = useState<TabName>("Overview");

  return (
    <div>
      <div
        role="tablist"
        style={{
          display: "flex",
          gap: "var(--space-1)",
          borderBottom: "1px solid var(--color-border)",
          overflowX: "auto",
        }}
      >
        {TAB_NAMES.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            className="tab-button"
            onClick={() => setActiveTab(tab)}
            style={{
              padding: "var(--space-3) var(--space-4)",
              border: "none",
              borderBottom: `2px solid ${activeTab === tab ? "var(--color-brand)" : "transparent"}`,
              background: "transparent",
              color: activeTab === tab ? "var(--color-text-primary)" : "var(--color-text-secondary)",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
              transition: "color 0.15s ease, border-color 0.15s ease",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div key={activeTab} className="fade-in" style={{ padding: "var(--space-5) 0" }}>
        {activeTab === "Overview" && <OverviewTab result={result} />}
        {activeTab === "Intent" && <IntentTab intentIr={result.intent_ir} />}
        {activeTab === "System Design" && <SystemDesignTab systemDesign={result.system_design} />}
        {activeTab === "Schema" && <SchemaTab dataSchema={result.data_schema} />}
        {activeTab === "Validation" && <ValidationTab validationReport={result.validation_report} />}
        {activeTab === "Raw JSON" && <RawJsonTab result={result} />}
      </div>
    </div>
  );
}
