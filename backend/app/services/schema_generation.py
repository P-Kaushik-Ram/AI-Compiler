"""Deterministic, rule-based implementation of the Schema Generation compiler stage.

This module converts a Stage 1 ``IntentIR`` plus a Stage 2 ``SystemDesign`` into a
``DataSchema`` — concrete entities, fields, relationships, and constraints — without
emitting any database-specific DDL, ORM model, or configuration. Stage 3 depends only on
``app.models.intent``, ``app.models.system_design``, and ``app.models.data_schema``; it
does not import anything from the Stage 1 or Stage 2 *services*, keeping it independently
testable and swappable.
"""
import re
import uuid

from app.models.data_schema import (
    DataSchema,
    DataSchemaStatus,
    SchemaAmbiguity,
    SchemaConstraint,
    SchemaEntity,
    SchemaField,
    SchemaRelationship,
)
from app.models.intent import Attribute, Entity, IntentIR, Relationship
from app.models.system_design import SystemDesign
from app.services import schema_generation_rules as rules

SCHEMA_VERSION = "1.0"


def _to_snake_case(name: str) -> str:
    """Convert a PascalCase or mixed-case entity name into snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class SchemaGenerationService:
    """Builds a DataSchema from an IntentIR and a SystemDesign using fixed, deterministic rules."""

    def generate(self, intent_ir: IntentIR, system_design: SystemDesign) -> DataSchema:
        """Run the full Schema Generation pipeline and return a complete DataSchema."""
        if system_design.status != "complete":
            return self._build_rejected_schema(intent_ir, system_design)

        module_by_entity = self._map_entities_to_modules(system_design)
        entities_by_name = {entity.name: entity for entity in intent_ir.entities}

        ambiguities: list[SchemaAmbiguity] = self._propagate_design_ambiguities(system_design)

        schema_entities: dict[str, SchemaEntity] = {}
        for entity_name, module_name in module_by_entity.items():
            entity = entities_by_name.get(entity_name)
            if entity is None:
                ambiguities.append(
                    SchemaAmbiguity(
                        question=f"Entity '{entity_name}' is referenced by SystemDesign but missing "
                        "from IntentIR; it was skipped.",
                        related_field="entities",
                        severity="advisory",
                    )
                )
                continue
            schema_entity, field_ambiguities = self._build_entity(entity, module_name, system_design)
            schema_entities[entity.name] = schema_entity
            ambiguities.extend(field_ambiguities)

        relationships, relationship_ambiguities = self._build_relationships(
            intent_ir.relationships, schema_entities
        )
        ambiguities.extend(relationship_ambiguities)

        constraints = self._build_constraints(system_design, module_by_entity)

        status = self._determine_status(ambiguities)
        confidence = self._compute_confidence(ambiguities)

        return DataSchema(
            schema_id=str(uuid.uuid4()),
            version=SCHEMA_VERSION,
            source_intent_id=intent_ir.intent_id,
            source_design_id=system_design.design_id,
            entities=list(schema_entities.values()),
            relationships=relationships,
            constraints=constraints,
            schema_ambiguities=ambiguities,
            confidence=confidence,
            status=status,
        )

    def _build_rejected_schema(self, intent_ir: IntentIR, system_design: SystemDesign) -> DataSchema:
        """Build the fixed DataSchema returned when the source SystemDesign is not complete."""
        return DataSchema(
            schema_id=str(uuid.uuid4()),
            version=SCHEMA_VERSION,
            source_intent_id=intent_ir.intent_id,
            source_design_id=system_design.design_id,
            confidence=0.0,
            status="rejected",
            schema_ambiguities=[
                SchemaAmbiguity(
                    question="Cannot perform Schema Generation on a SystemDesign with "
                    f"status='{system_design.status}'. Resolve Stage 2 ambiguities first.",
                    related_field="status",
                    severity="blocking",
                )
            ],
        )

    def _map_entities_to_modules(self, system_design: SystemDesign) -> dict[str, str]:
        """Build a mapping of entity name to owning module name from the SystemDesign's modules."""
        mapping: dict[str, str] = {}
        for module in system_design.modules:
            for entity_name in module.owned_entities:
                mapping[entity_name] = module.name
        return mapping

    def _propagate_design_ambiguities(self, system_design: SystemDesign) -> list[SchemaAmbiguity]:
        """Carry forward any unresolved Stage 2 ambiguities so they remain visible at Stage 3."""
        return [
            SchemaAmbiguity(
                question=f"[Carried from System Design] {ambiguity.question}",
                related_field=ambiguity.related_field,
                severity=ambiguity.severity,
            )
            for ambiguity in system_design.design_ambiguities
        ]

    def _build_entity(
        self, entity: Entity, module_name: str, system_design: SystemDesign
    ) -> tuple[SchemaEntity, list[SchemaAmbiguity]]:
        """Build a SchemaEntity (with a synthesized primary key) from one IntentIR entity."""
        ambiguities: list[SchemaAmbiguity] = []
        fields = [
            SchemaField(name="id", data_type="uuid", is_nullable=False, is_primary_key=True, is_unique=True)
        ]
        for attribute in entity.attributes:
            field, ambiguity = self._build_field(entity.name, attribute, module_name, system_design)
            fields.append(field)
            if ambiguity is not None:
                ambiguities.append(ambiguity)

        schema_entity = SchemaEntity(
            name=_to_snake_case(entity.name),
            source_entity=entity.name,
            module=module_name,
            primary_key="id",
            fields=fields,
        )
        return schema_entity, ambiguities

    def _build_field(
        self, entity_name: str, attribute: Attribute, module_name: str, system_design: SystemDesign
    ) -> tuple[SchemaField, SchemaAmbiguity | None]:
        """Build a SchemaField from one IntentIR attribute, with type defaulting and sensitivity tagging."""
        ambiguity: SchemaAmbiguity | None = None
        data_type = rules.TYPE_HINT_MAP.get(attribute.type_hint)
        if data_type is None:
            data_type = rules.DEFAULT_DATA_TYPE
            ambiguity = SchemaAmbiguity(
                question=f"Unknown type_hint '{attribute.type_hint}' for "
                f"'{entity_name}.{attribute.name}'; defaulted to '{rules.DEFAULT_DATA_TYPE}'.",
                related_field=f"entities[{entity_name}].fields[{attribute.name}]",
                severity="advisory",
            )

        is_sensitive = attribute.name in rules.PII_ATTRIBUTE_NAMES or self._entity_flagged_by_risk(
            module_name, system_design
        )

        field = SchemaField(
            name=attribute.name,
            data_type=data_type,  # type: ignore[arg-type]
            is_nullable=attribute.is_optional,
            is_primary_key=False,
            is_unique=attribute.name in rules.UNIQUE_FIELD_NAMES,
            is_sensitive=is_sensitive,
            source_attribute=attribute.name,
        )
        return field, ambiguity

    def _entity_flagged_by_risk(self, module_name: str, system_design: SystemDesign) -> bool:
        """Return True if the module owning this entity is affected by a sensitive-category design risk."""
        return any(
            module_name in risk.affected_modules and risk.category in rules.SENSITIVE_RISK_CATEGORIES
            for risk in system_design.design_risks
        )

    def _build_relationships(
        self, relationships: list[Relationship], schema_entities: dict[str, SchemaEntity]
    ) -> tuple[list[SchemaRelationship], list[SchemaAmbiguity]]:
        """Build SchemaRelationships from IR relationships, flagging conflicting cardinalities."""
        ambiguities: list[SchemaAmbiguity] = []
        groups: dict[tuple[str, str], list[Relationship]] = {}
        for rel in relationships:
            key = tuple(sorted((rel.from_entity, rel.to_entity)))
            groups.setdefault(key, []).append(rel)

        schema_relationships: list[SchemaRelationship] = []
        for (entity_a, entity_b), group in groups.items():
            distinct_types = {rel.relationship_type for rel in group}
            if len(distinct_types) > 1:
                ambiguities.append(
                    SchemaAmbiguity(
                        question=f"Conflicting relationship types ({', '.join(sorted(distinct_types))}) "
                        f"found between '{entity_a}' and '{entity_b}'; no relationship was generated.",
                        related_field="relationships",
                        severity="blocking",
                    )
                )
                continue

            rel = group[0]
            if rel.from_entity not in schema_entities or rel.to_entity not in schema_entities:
                continue

            schema_relationship, relationship_ambiguity = self._build_single_relationship(rel)
            schema_relationships.append(schema_relationship)
            if relationship_ambiguity is not None:
                ambiguities.append(relationship_ambiguity)

        return schema_relationships, ambiguities

    def _build_single_relationship(self, rel: Relationship) -> tuple[SchemaRelationship, SchemaAmbiguity | None]:
        """Build one SchemaRelationship, deriving cardinality and a foreign-key field where applicable."""
        cardinality, swap = rules.RELATIONSHIP_CARDINALITY_MAP[rel.relationship_type]
        parent_entity, child_entity = (rel.to_entity, rel.from_entity) if swap else (rel.from_entity, rel.to_entity)

        ambiguity: SchemaAmbiguity | None = None
        foreign_key_field: str | None = None
        if cardinality != "many_to_many":
            if rel.from_entity == rel.to_entity:
                foreign_key_field = f"related_{_to_snake_case(parent_entity)}_id"
                ambiguity = SchemaAmbiguity(
                    question=f"Self-referential relationship detected on '{rel.from_entity}'; "
                    f"the generated foreign key field '{foreign_key_field}' may need manual review.",
                    related_field=f"relationships[{rel.from_entity}->{rel.to_entity}]",
                    severity="advisory",
                )
            else:
                foreign_key_field = f"{_to_snake_case(parent_entity)}_id"

        name = f"{_to_snake_case(rel.from_entity)}_{rel.relationship_type}_{_to_snake_case(rel.to_entity)}"
        relationship = SchemaRelationship(
            name=name,
            from_entity=_to_snake_case(rel.from_entity),
            to_entity=_to_snake_case(rel.to_entity),
            cardinality=cardinality,  # type: ignore[arg-type]
            foreign_key_field=foreign_key_field,
            source_relationship_type=rel.relationship_type,
        )
        return relationship, ambiguity

    def _build_constraints(
        self, system_design: SystemDesign, module_by_entity: dict[str, str]
    ) -> list[SchemaConstraint]:
        """Build SchemaConstraints from high/critical design risks, one per affected entity."""
        constraints: list[SchemaConstraint] = []
        seen: set[tuple[str, str]] = set()
        for risk in system_design.design_risks:
            if risk.severity not in rules.CONSTRAINT_TRIGGER_SEVERITIES:
                continue
            constraint_type = rules.RISK_CONSTRAINT_TYPE_MAP.get(risk.category)
            if constraint_type is None:
                continue
            affected_entities = [
                entity_name
                for entity_name, module_name in module_by_entity.items()
                if module_name in risk.affected_modules
            ]
            for entity_name in affected_entities:
                schema_entity_name = _to_snake_case(entity_name)
                key = (schema_entity_name, constraint_type)
                if key in seen:
                    continue
                seen.add(key)
                constraints.append(
                    SchemaConstraint(
                        entity=schema_entity_name,
                        field=None,
                        constraint_type=constraint_type,  # type: ignore[arg-type]
                        description=risk.description,
                        source_risk_category=risk.category,
                    )
                )
        return constraints

    def _determine_status(self, ambiguities: list[SchemaAmbiguity]) -> DataSchemaStatus:
        """Return 'needs_clarification' if any ambiguity is blocking, otherwise 'complete'."""
        if any(a.severity == "blocking" for a in ambiguities):
            return "needs_clarification"
        return "complete"

    def _compute_confidence(self, ambiguities: list[SchemaAmbiguity]) -> float:
        """Start from a high baseline and subtract for each ambiguity surfaced during generation."""
        confidence = 0.9
        for ambiguity in ambiguities:
            confidence -= 0.3 if ambiguity.severity == "blocking" else 0.1
        return round(max(confidence, 0.1), 2)
