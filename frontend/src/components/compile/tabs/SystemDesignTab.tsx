import { Network } from "lucide-react";
import type { SystemDesign } from "../../../types/systemDesign";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { StatusPill } from "../../common/StatusPill";
import { formatConfidence, formatLabel, severityToVariant, statusToKind } from "../../../lib/status";
import { ListSection, TabRow } from "./shared";

interface SystemDesignTabProps {
  systemDesign: SystemDesign | null;
}

export function SystemDesignTab({ systemDesign }: SystemDesignTabProps) {
  if (!systemDesign) {
    return (
      <EmptyState
        icon={Network}
        title="System Design stage not reached"
        description="This compilation did not produce a SystemDesign."
      />
    );
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-6)", flexWrap: "wrap" }}>
        <Badge variant="brand">{formatLabel(systemDesign.architecture_style)}</Badge>
        <StatusPill label={systemDesign.status} status={statusToKind(systemDesign.status)} />
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
          {formatConfidence(systemDesign.confidence)} confidence
        </span>
      </div>

      <ListSection
        title="Modules"
        items={systemDesign.modules}
        emptyLabel="No modules defined."
        renderItem={(module) => (
          <TabRow key={module.name}>
            <strong style={{ fontSize: 13 }}>{module.name}</strong>
            <p style={{ margin: "4px 0 var(--space-2)", color: "var(--color-text-secondary)" }}>{module.purpose}</p>
            {module.owned_entities.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
                {module.owned_entities.map((entity) => (
                  <Badge key={entity} variant="neutral">
                    {entity}
                  </Badge>
                ))}
              </div>
            )}
          </TabRow>
        )}
      />

      <ListSection
        title="Capabilities"
        items={systemDesign.capabilities}
        emptyLabel="No capabilities defined."
        renderItem={(capability) => (
          <TabRow key={capability.name}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13 }}>{capability.name}</strong>
              <Badge variant="neutral">{capability.module}</Badge>
              {capability.risk_level !== "none" && (
                <Badge variant={severityToVariant(capability.risk_level)}>{capability.risk_level} risk</Badge>
              )}
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{capability.description}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Workflows"
        items={systemDesign.workflows}
        emptyLabel="No multi-step workflows synthesized."
        renderItem={(workflow) => (
          <TabRow key={workflow.name}>
            <strong style={{ fontSize: 13 }}>{workflow.name}</strong>
            <p style={{ margin: "4px 0 var(--space-2)", color: "var(--color-text-secondary)" }}>
              Trigger: {workflow.trigger} → {workflow.outcome}
            </p>
            {workflow.steps.length > 0 && (
              <ol style={{ margin: 0, paddingLeft: 18, color: "var(--color-text-secondary)" }}>
                {workflow.steps.map((step) => (
                  <li key={step.step_name}>{step.capability}</li>
                ))}
              </ol>
            )}
          </TabRow>
        )}
      />

      <ListSection
        title="Actors"
        items={systemDesign.actors}
        emptyLabel="No actors defined."
        renderItem={(actor) => (
          <TabRow key={actor.name}>
            <strong style={{ fontSize: 13 }}>{actor.name}</strong>
            <p style={{ margin: "4px 0 var(--space-2)", color: "var(--color-text-secondary)" }}>{actor.description}</p>
            {actor.accessible_capabilities.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
                {actor.accessible_capabilities.map((capability) => (
                  <Badge key={capability} variant="neutral">
                    {capability}
                  </Badge>
                ))}
              </div>
            )}
          </TabRow>
        )}
      />

      <ListSection
        title="Module Dependencies"
        items={systemDesign.module_dependencies}
        emptyLabel="No inter-module dependencies."
        renderItem={(dependency, index) => (
          <TabRow key={index}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13 }}>
                {dependency.from_module} → {dependency.to_module}
              </strong>
              <Badge variant="neutral">{dependency.dependency_type}</Badge>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{dependency.reason}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="External Dependencies"
        items={systemDesign.external_dependencies}
        emptyLabel="No external dependencies referenced."
        renderItem={(dependency) => (
          <TabRow key={dependency.name}>
            <strong style={{ fontSize: 13 }}>{dependency.name}</strong>
            <span style={{ marginLeft: "var(--space-2)", color: "var(--color-text-secondary)" }}>
              {dependency.purpose} — owned by {dependency.owning_module}
            </span>
          </TabRow>
        )}
      />

      <ListSection
        title="Design Ambiguities"
        items={systemDesign.design_ambiguities}
        emptyLabel="No open design ambiguities."
        renderItem={(ambiguity, index) => (
          <TabRow key={index}>
            <Badge variant={severityToVariant(ambiguity.severity)}>{formatLabel(ambiguity.severity)}</Badge>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{ambiguity.question}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Design Risks"
        items={systemDesign.design_risks}
        emptyLabel="No design risks recorded."
        renderItem={(risk, index) => (
          <TabRow key={index}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <Badge variant={severityToVariant(risk.severity)}>{formatLabel(risk.category)}</Badge>
              <span style={{ fontWeight: 600, fontSize: 11, textTransform: "uppercase" }}>{risk.severity}</span>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{risk.architectural_implication}</p>
          </TabRow>
        )}
      />
    </div>
  );
}
