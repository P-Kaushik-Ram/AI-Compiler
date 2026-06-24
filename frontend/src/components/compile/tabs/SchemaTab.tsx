import { Database } from "lucide-react";
import type { DataSchema, SchemaField } from "../../../types/dataSchema";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { StatusPill } from "../../common/StatusPill";
import { formatConfidence, formatLabel, statusToKind } from "../../../lib/status";
import { ListSection, TabRow } from "./shared";

interface SchemaTabProps {
  dataSchema: DataSchema | null;
}

export function SchemaTab({ dataSchema }: SchemaTabProps) {
  if (!dataSchema) {
    return (
      <EmptyState
        icon={Database}
        title="Schema Generation stage not reached"
        description="This compilation did not produce a DataSchema."
      />
    );
  }

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-6)", flexWrap: "wrap" }}>
        <StatusPill label={dataSchema.status} status={statusToKind(dataSchema.status)} />
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
          {formatConfidence(dataSchema.confidence)} confidence
        </span>
      </div>

      <ListSection
        title="Entities"
        items={dataSchema.entities}
        emptyLabel="No schema entities generated."
        renderItem={(entity) => (
          <TabRow key={entity.name}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13, fontFamily: "var(--font-mono)" }}>{entity.name}</strong>
              <Badge variant="neutral">{entity.module}</Badge>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: "var(--space-2)" }}>
              {entity.fields.map((field) => (
                <FieldRow key={field.name} field={field} />
              ))}
            </div>
          </TabRow>
        )}
      />

      <ListSection
        title="Relationships"
        items={dataSchema.relationships}
        emptyLabel="No schema relationships generated."
        renderItem={(relationship) => (
          <TabRow key={relationship.name}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <strong style={{ fontSize: 13 }}>
                {relationship.from_entity} → {relationship.to_entity}
              </strong>
              <Badge variant="neutral">{formatLabel(relationship.cardinality)}</Badge>
            </div>
            {relationship.foreign_key_field && (
              <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
                FK: {relationship.foreign_key_field}
              </p>
            )}
          </TabRow>
        )}
      />

      <ListSection
        title="Constraints"
        items={dataSchema.constraints}
        emptyLabel="No cross-cutting constraints generated."
        renderItem={(constraint, index) => (
          <TabRow key={index}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <Badge variant="warning">{formatLabel(constraint.constraint_type)}</Badge>
              <strong style={{ fontSize: 13 }}>
                {constraint.entity}
                {constraint.field ? `.${constraint.field}` : ""}
              </strong>
            </div>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{constraint.description}</p>
          </TabRow>
        )}
      />

      <ListSection
        title="Schema Ambiguities"
        items={dataSchema.schema_ambiguities}
        emptyLabel="No open schema ambiguities."
        renderItem={(ambiguity, index) => (
          <TabRow key={index}>
            <Badge variant={ambiguity.severity === "blocking" ? "error" : "warning"}>{formatLabel(ambiguity.severity)}</Badge>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)" }}>{ambiguity.question}</p>
          </TabRow>
        )}
      />
    </div>
  );
}

function FieldRow({ field }: { field: SchemaField }) {
  const flags: string[] = [];
  if (field.is_primary_key) flags.push("PK");
  if (field.is_unique) flags.push("unique");
  if (field.is_nullable) flags.push("nullable");
  if (field.is_sensitive) flags.push("sensitive");

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
      <span style={{ fontFamily: "var(--font-mono)" }}>{field.name}</span>
      <span style={{ color: "var(--color-text-secondary)" }}>{field.data_type}</span>
      {flags.map((flag) => (
        <Badge key={flag} variant={flag === "sensitive" ? "error" : "neutral"}>
          {flag}
        </Badge>
      ))}
    </div>
  );
}
