/** Mirrors backend/app/models/data_schema.py */

export type DataType = "string" | "integer" | "float" | "boolean" | "date" | "datetime" | "uuid";
export type Cardinality = "one_to_one" | "one_to_many" | "many_to_many";
export type ConstraintType = "requires_encryption" | "requires_audit_log" | "unique_together" | "other";
export type DataSchemaStatus = "complete" | "needs_clarification" | "rejected";
export type SchemaAmbiguitySeverity = "blocking" | "advisory";

export interface SchemaField {
  name: string;
  data_type: DataType;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_unique: boolean;
  is_sensitive: boolean;
  source_attribute: string | null;
}

export interface SchemaEntity {
  name: string;
  source_entity: string;
  module: string;
  primary_key: string;
  fields: SchemaField[];
}

export interface SchemaRelationship {
  name: string;
  from_entity: string;
  to_entity: string;
  cardinality: Cardinality;
  foreign_key_field: string | null;
  source_relationship_type: string;
}

export interface SchemaConstraint {
  entity: string;
  field: string | null;
  constraint_type: ConstraintType;
  description: string;
  source_risk_category: string | null;
}

export interface SchemaAmbiguity {
  question: string;
  related_field: string | null;
  severity: SchemaAmbiguitySeverity;
}

export interface DataSchema {
  schema_id: string;
  version: string;
  source_intent_id: string;
  source_design_id: string;
  entities: SchemaEntity[];
  relationships: SchemaRelationship[];
  constraints: SchemaConstraint[];
  schema_ambiguities: SchemaAmbiguity[];
  confidence: number;
  status: DataSchemaStatus;
}
