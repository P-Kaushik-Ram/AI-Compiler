import { FileQuestion } from "lucide-react";
import type { IntentIR } from "../../../types/intent";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { StatusPill } from "../../common/StatusPill";
import { formatConfidence, formatLabel, severityToVariant, statusToKind } from "../../../lib/status";
import { ListSection, TabRow } from "./shared";

interface IntentTabProps {
  intentIr: IntentIR | null;
}

export function IntentTab({ intentIr }: IntentTabProps) {
  if (!intentIr) {
    return (
      <EmptyState
        icon={FileQuestion}
        title="Intent stage not reached"
        description="This compilation did not produce an IntentIR."
      />
    );
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-2)", flexWrap: "wrap" }}>
        <Badge variant="brand">{intentIr.domain}</Badge>
        <StatusPill label={intentIr.status} status={statusToKind(intentIr.status)} />
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
          {formatConfidence(intentIr.confidence)} confidence
        </span>
      </div>
      <p style={{ margin: "0 0 var(--space-6)", fontSize: 13, color: "var(--color-text-secondary)" }}>
        {intentIr.domain_summary}
      </p>

      <ListSection
        title="Entities"
        items={intentIr.entities}
        emptyLabel="No entities detected."
        renderItem={(entity) => (
          <TabRow key={entity.name}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <strong style={{ fontSize: 13 }}>{entity.name}</strong>
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-secondary)" }}>
                {formatConfidence(entity.confidence)}
              </span>
            </div>
            <p style={{ margin: "4px 0 var(--space-2)", color: "var(--color-text-secondary)" }}>{entity.description}</p>
            {entity.attributes.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>
                {entity.attributes.map((attribute) => (
                  <Badge key={attribute.name} variant="neutral">
                    {attribute.name}: {attribute.type_hint}
                    {attribute.is_optional ? "?" : ""}
                  </Badge>
                ))}
              </div>
            )}
          </TabRow>
        )}
      />

      <ListSection
        title="Relationships"
        items={intentIr.relationships}
        emptyLabel="No relationships detected."
        renderItem={(relationship, index) => (
          <TabRow key={`${relationship.from_entity}-${relationship.to_entity}-${index}`}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13 }}>
                {relationship.from_entity} → {relationship.to_entity}
              </strong>
              <Badge variant="neutral">{formatLabel(relationship.relationship_type)}</Badge>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{relationship.description}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Actions"
        items={intentIr.actions}
        emptyLabel="No actions detected."
        renderItem={(action) => (
          <TabRow key={action.name}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13 }}>{action.name}</strong>
              {action.target_entity && <Badge variant="neutral">{action.target_entity}</Badge>}
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-secondary)" }}>
                {formatConfidence(action.confidence)}
              </span>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{action.description}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="User Stories"
        items={intentIr.user_stories}
        emptyLabel="No user stories derived."
        renderItem={(story, index) => (
          <TabRow key={`${story.actor}-${index}`}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13 }}>{story.actor}</strong>
              <Badge variant={story.priority === "must_have" ? "brand" : "neutral"}>{formatLabel(story.priority)}</Badge>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{story.goal}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Functional Requirements"
        items={intentIr.functional_requirements}
        emptyLabel="No explicit functional requirements detected."
        renderItem={(requirement, index) => <TabRow key={index}>{requirement.description}</TabRow>}
      />

      <ListSection
        title="Non-Functional Requirements"
        items={intentIr.non_functional_requirements}
        emptyLabel="No non-functional requirements detected."
        renderItem={(requirement, index) => (
          <TabRow key={index}>
            <Badge variant="info">{formatLabel(requirement.category)}</Badge>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{requirement.description}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Integrations"
        items={intentIr.integrations}
        emptyLabel="No third-party integrations referenced."
        renderItem={(integration) => (
          <TabRow key={integration.name}>
            <strong style={{ fontSize: 13 }}>{integration.name}</strong>
            <span style={{ marginLeft: "var(--space-2)", color: "var(--color-text-secondary)" }}>{integration.purpose}</span>
          </TabRow>
        )}
      />

      <ListSection
        title="Risk Flags"
        items={intentIr.risk_flags}
        emptyLabel="No risks flagged."
        renderItem={(risk, index) => (
          <TabRow key={index}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <Badge variant={severityToVariant(risk.severity)}>{formatLabel(risk.category)}</Badge>
              <span style={{ fontWeight: 600, fontSize: 11, textTransform: "uppercase" }}>{risk.severity}</span>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{risk.description}</p>
            {risk.recommended_handling && (
              <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)", fontStyle: "italic" }}>
                {risk.recommended_handling}
              </p>
            )}
          </TabRow>
        )}
      />

      <ListSection
        title="Ambiguities"
        items={intentIr.ambiguities}
        emptyLabel="No open ambiguities."
        renderItem={(ambiguity, index) => (
          <TabRow key={index}>
            <Badge variant={severityToVariant(ambiguity.severity)}>{formatLabel(ambiguity.severity)}</Badge>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{ambiguity.question}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Assumptions"
        items={intentIr.assumptions}
        emptyLabel="No assumptions were made."
        renderItem={(assumption, index) => (
          <TabRow key={index}>
            <p style={{ margin: 0 }}>{assumption.description}</p>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)", fontStyle: "italic" }}>
              {assumption.rationale}
            </p>
          </TabRow>
        )}
      />
    </div>
  );
}
