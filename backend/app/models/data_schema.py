"""Pydantic models for the Schema Generation stage's DataSchema output."""
from typing import Literal

from pydantic import BaseModel, Field

DataType = Literal["string", "integer", "float", "boolean", "date", "datetime", "uuid"]
Cardinality = Literal["one_to_one", "one_to_many", "many_to_many"]
ConstraintType = Literal["requires_encryption", "requires_audit_log", "unique_together", "other"]
DataSchemaStatus = Literal["complete", "needs_clarification", "rejected"]


class SchemaField(BaseModel):
    """A single concrete field on a SchemaEntity."""

    name: str
    data_type: DataType
    is_nullable: bool
    is_primary_key: bool = False
    is_unique: bool = False
    is_sensitive: bool = False
    source_attribute: str | None = None


class SchemaEntity(BaseModel):
    """The concrete, table/collection-shaped record generated from one IntentIR entity."""

    name: str
    source_entity: str
    module: str
    primary_key: str
    fields: list[SchemaField] = Field(default_factory=list)


class SchemaRelationship(BaseModel):
    """A concrete, cardinality-bearing relationship between two SchemaEntities."""

    name: str
    from_entity: str
    to_entity: str
    cardinality: Cardinality
    foreign_key_field: str | None = None
    source_relationship_type: str


class SchemaConstraint(BaseModel):
    """A cross-cutting rule (e.g. encryption, audit logging) attached to an entity or field."""

    entity: str
    field: str | None = None
    constraint_type: ConstraintType
    description: str
    source_risk_category: str | None = None


class SchemaAmbiguity(BaseModel):
    """An unresolved schema-generation decision that may require clarification."""

    question: str
    related_field: str | None = None
    severity: Literal["blocking", "advisory"]


class DataSchema(BaseModel):
    """The complete logical data schema produced by the Schema Generation stage."""

    schema_id: str
    version: str
    source_intent_id: str
    source_design_id: str
    entities: list[SchemaEntity] = Field(default_factory=list)
    relationships: list[SchemaRelationship] = Field(default_factory=list)
    constraints: list[SchemaConstraint] = Field(default_factory=list)
    schema_ambiguities: list[SchemaAmbiguity] = Field(default_factory=list)
    confidence: float
    status: DataSchemaStatus
