"""Deterministic, rule-based implementation of the Validation & Repair compiler stage.

This module cross-checks a Stage 1 ``IntentIR``, a Stage 2 ``SystemDesign``, and a Stage 3
``DataSchema`` against one another and produces a ``ValidationReport``. It never mutates any
of the three artifacts it receives — it only reports findings, recommends remediation, and
computes a single deterministic decision about whether the pipeline may proceed. It imports
only from ``app.models.*`` and ``app.services.*_rules`` (read-only constants), not from the
Stage 1-3 *services*, keeping it independently testable.
"""
import re
import uuid

from app.models.data_schema import DataSchema
from app.models.intent import IntentIR
from app.models.system_design import SystemDesign
from app.models.validation import (
    ConsistencySummary,
    PipelineDecision,
    ValidationFinding,
    ValidationReport,
    ValidationStatus,
)
from app.services import validation_rules as rules

REPORT_VERSION = "1.0"


def _to_snake_case(name: str) -> str:
    """Convert a PascalCase or mixed-case entity name into snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class ValidationService:
    """Performs read-only, deterministic cross-stage validation over the compiler's artifacts."""

    def validate(self, intent_ir: IntentIR, system_design: SystemDesign, data_schema: DataSchema) -> ValidationReport:
        """Run every validation category and return a complete, deterministic ValidationReport."""
        findings: list[ValidationFinding] = []
        findings.extend(self._check_cascade_status(intent_ir, system_design, data_schema))
        findings.extend(self._check_traceability(intent_ir, system_design, data_schema))
        findings.extend(self._check_missing_entities(intent_ir, system_design, data_schema))
        findings.extend(self._check_duplicate_definitions(system_design, data_schema))
        findings.extend(self._check_naming_conflicts(intent_ir, data_schema))
        findings.extend(self._check_invalid_references(system_design, data_schema))

        orphan_findings, acknowledged_gaps = self._check_orphan_relationships(intent_ir, data_schema)
        findings.extend(orphan_findings)

        findings.extend(self._check_risk_propagation(intent_ir, system_design, data_schema))
        findings.extend(self._check_missing_required_fields(intent_ir, data_schema))

        self._assign_finding_ids(findings)

        confidence = self._compute_confidence(intent_ir, system_design, data_schema, findings)
        pipeline_decision, status = self._determine_decision(intent_ir, system_design, data_schema, findings)

        summary = ConsistencySummary(
            entities_checked=len(intent_ir.entities),
            relationships_checked=len(intent_ir.relationships),
            modules_checked=len(system_design.modules),
            schema_entities_checked=len(data_schema.entities),
            upstream_ambiguities_carried=(
                len(intent_ir.ambiguities) + len(system_design.design_ambiguities) + len(data_schema.schema_ambiguities)
            ),
            acknowledged_gaps=acknowledged_gaps,
        )

        return ValidationReport(
            validation_id=str(uuid.uuid4()),
            version=REPORT_VERSION,
            source_intent_id=intent_ir.intent_id,
            source_design_id=system_design.design_id,
            source_schema_id=data_schema.schema_id,
            findings=findings,
            consistency_summary=summary,
            confidence=confidence,
            pipeline_decision=pipeline_decision,
            status=status,
        )

    def _assign_finding_ids(self, findings: list[ValidationFinding]) -> None:
        """Assign deterministic, sequential IDs to findings in the order they were discovered."""
        for index, finding in enumerate(findings, start=1):
            finding.finding_id = f"finding-{index:03d}"

    def _check_cascade_status(
        self, intent_ir: IntentIR, system_design: SystemDesign, data_schema: DataSchema
    ) -> list[ValidationFinding]:
        """Flag any upstream artifact whose own status is not 'complete'."""
        findings: list[ValidationFinding] = []
        stages = (("intent", intent_ir.status), ("system_design", system_design.status), ("data_schema", data_schema.status))
        for stage_name, stage_status in stages:
            if stage_status != "complete":
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="cross_stage_inconsistency",
                        severity="critical",
                        stage=stage_name,  # type: ignore[arg-type]
                        message=f"Stage '{stage_name}' has status='{stage_status}', not 'complete'.",
                        related_field="status",
                        recommendation=f"Resolve the ambiguities reported by the '{stage_name}' stage and "
                        "re-run the pipeline from that stage before validating further.",
                    )
                )
        return findings

    def _check_traceability(
        self, intent_ir: IntentIR, system_design: SystemDesign, data_schema: DataSchema
    ) -> list[ValidationFinding]:
        """Verify the document-level traceability chain: design->intent and schema->design->intent."""
        findings: list[ValidationFinding] = []
        if system_design.source_intent_id != intent_ir.intent_id:
            findings.append(
                ValidationFinding(
                    finding_id="",
                    category="broken_traceability",
                    severity="critical",
                    stage="system_design",
                    message="SystemDesign.source_intent_id does not match the provided IntentIR.intent_id.",
                    related_field="source_intent_id",
                    recommendation="Confirm the SystemDesign was generated from this exact IntentIR.",
                )
            )
        if data_schema.source_intent_id != intent_ir.intent_id:
            findings.append(
                ValidationFinding(
                    finding_id="",
                    category="broken_traceability",
                    severity="critical",
                    stage="data_schema",
                    message="DataSchema.source_intent_id does not match the provided IntentIR.intent_id.",
                    related_field="source_intent_id",
                    recommendation="Confirm the DataSchema was generated from this exact IntentIR.",
                )
            )
        if data_schema.source_design_id != system_design.design_id:
            findings.append(
                ValidationFinding(
                    finding_id="",
                    category="broken_traceability",
                    severity="critical",
                    stage="data_schema",
                    message="DataSchema.source_design_id does not match the provided SystemDesign.design_id.",
                    related_field="source_design_id",
                    recommendation="Confirm the DataSchema was generated from this exact SystemDesign.",
                )
            )

        entity_names = {entity.name for entity in intent_ir.entities}
        action_names = {action.name for action in intent_ir.actions}
        for entity in data_schema.entities:
            if entity.source_entity not in entity_names:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="broken_traceability",
                        severity="critical",
                        stage="data_schema",
                        message=f"SchemaEntity '{entity.name}' traces to source_entity "
                        f"'{entity.source_entity}', which does not exist in IntentIR.entities.",
                        related_field=f"entities[{entity.name}].source_entity",
                        recommendation="Regenerate the DataSchema from the current IntentIR.",
                    )
                )
                continue
            attribute_names = {a.name for a in next(e for e in intent_ir.entities if e.name == entity.source_entity).attributes}
            for field in entity.fields:
                if field.source_attribute is not None and field.source_attribute not in attribute_names:
                    findings.append(
                        ValidationFinding(
                            finding_id="",
                            category="broken_traceability",
                            severity="error",
                            stage="data_schema",
                            message=f"SchemaField '{entity.name}.{field.name}' traces to source_attribute "
                            f"'{field.source_attribute}', which does not exist on IntentIR entity "
                            f"'{entity.source_entity}'.",
                            related_field=f"entities[{entity.name}].fields[{field.name}].source_attribute",
                            recommendation="Regenerate the DataSchema from the current IntentIR.",
                        )
                    )

        for capability in system_design.capabilities:
            for related_action in capability.related_actions:
                if related_action not in action_names:
                    findings.append(
                        ValidationFinding(
                            finding_id="",
                            category="broken_traceability",
                            severity="error",
                            stage="system_design",
                            message=f"Capability '{capability.name}' references action '{related_action}', "
                            "which does not exist in IntentIR.actions.",
                            related_field=f"capabilities[{capability.name}].related_actions",
                            recommendation="Regenerate the SystemDesign from the current IntentIR.",
                        )
                    )
        return findings

    def _check_missing_entities(
        self, intent_ir: IntentIR, system_design: SystemDesign, data_schema: DataSchema
    ) -> list[ValidationFinding]:
        """Verify every IntentIR entity has a home in both SystemDesign and DataSchema."""
        findings: list[ValidationFinding] = []
        owned_entities = {name for module in system_design.modules for name in module.owned_entities}
        schema_source_entities = {entity.source_entity for entity in data_schema.entities}

        for entity in intent_ir.entities:
            if entity.name not in owned_entities:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="missing_entity",
                        severity="critical",
                        stage="system_design",
                        message=f"IntentIR entity '{entity.name}' is not owned by any SystemDesign module.",
                        related_field=f"entities[{entity.name}]",
                        recommendation=f"Re-run System Design; '{entity.name}' must be assigned to a module.",
                    )
                )
            if entity.name not in schema_source_entities:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="missing_entity",
                        severity="critical",
                        stage="data_schema",
                        message=f"IntentIR entity '{entity.name}' has no corresponding SchemaEntity in DataSchema.",
                        related_field=f"entities[{entity.name}]",
                        recommendation=f"Re-run Schema Generation; '{entity.name}' should produce a SchemaEntity.",
                    )
                )
        return findings

    def _check_duplicate_definitions(
        self, system_design: SystemDesign, data_schema: DataSchema
    ) -> list[ValidationFinding]:
        """Detect duplicate module/capability/schema-entity names and multiply-owned entities."""
        findings: list[ValidationFinding] = []
        findings.extend(self._find_duplicates([m.name for m in system_design.modules], "module name", "system_design"))
        findings.extend(self._find_duplicates([c.name for c in system_design.capabilities], "capability name", "system_design"))
        findings.extend(self._find_duplicates([e.name for e in data_schema.entities], "schema entity name", "data_schema"))

        ownership_counts: dict[str, int] = {}
        for module in system_design.modules:
            for entity_name in module.owned_entities:
                ownership_counts[entity_name] = ownership_counts.get(entity_name, 0) + 1
        for entity_name, count in ownership_counts.items():
            if count > 1:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="duplicate_definition",
                        severity="critical",
                        stage="system_design",
                        message=f"Entity '{entity_name}' is owned by {count} different modules.",
                        related_field="modules",
                        recommendation=f"Re-run System Design; '{entity_name}' must be owned by exactly one module.",
                    )
                )
        return findings

    def _find_duplicates(self, names: list[str], label: str, stage: str) -> list[ValidationFinding]:
        """Return one duplicate_definition finding per name that appears more than once in ``names``."""
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)
        return [
            ValidationFinding(
                finding_id="",
                category="duplicate_definition",
                severity="critical",
                stage=stage,  # type: ignore[arg-type]
                message=f"Duplicate {label} '{name}' found.",
                related_field=None,
                recommendation=f"Ensure every {label} is unique before proceeding.",
            )
            for name in sorted(duplicates)
        ]

    def _check_naming_conflicts(self, intent_ir: IntentIR, data_schema: DataSchema) -> list[ValidationFinding]:
        """Detect schema names that drift from the deterministic snake_case convention, and name collisions."""
        findings: list[ValidationFinding] = []
        for entity in data_schema.entities:
            expected_name = _to_snake_case(entity.source_entity)
            if entity.name != expected_name:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="naming_conflict",
                        severity="warning",
                        stage="data_schema",
                        message=f"SchemaEntity '{entity.name}' does not match the expected snake_case "
                        f"name '{expected_name}' for source_entity '{entity.source_entity}'.",
                        related_field=f"entities[{entity.name}].name",
                        recommendation="Regenerate the DataSchema using the standard naming convention.",
                    )
                )

        snake_case_groups: dict[str, list[str]] = {}
        for entity in intent_ir.entities:
            snake_case_groups.setdefault(_to_snake_case(entity.name), []).append(entity.name)
        for snake_name, original_names in snake_case_groups.items():
            if len(original_names) > 1:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="naming_conflict",
                        severity="critical",
                        stage="cross_stage",
                        message=f"IntentIR entities {sorted(original_names)} all collide to the same "
                        f"schema name '{snake_name}'.",
                        related_field="entities",
                        recommendation="Rename one of the colliding entities in the IntentIR before "
                        "regenerating downstream artifacts.",
                    )
                )
        return findings

    def _check_invalid_references(self, system_design: SystemDesign, data_schema: DataSchema) -> list[ValidationFinding]:
        """Verify every cross-reference string within SystemDesign and DataSchema resolves to a real record."""
        findings: list[ValidationFinding] = []
        module_names = {m.name for m in system_design.modules}
        capability_names = {c.name for c in system_design.capabilities}
        schema_entity_names = {e.name for e in data_schema.entities}

        for capability in system_design.capabilities:
            if capability.module not in module_names:
                findings.append(self._invalid_reference("system_design", f"capabilities[{capability.name}].module", capability.module, "module"))
        for actor in system_design.actors:
            for capability_name in actor.accessible_capabilities:
                if capability_name not in capability_names:
                    findings.append(self._invalid_reference("system_design", f"actors[{actor.name}].accessible_capabilities", capability_name, "capability"))
        for workflow in system_design.workflows:
            for step in workflow.steps:
                if step.capability not in capability_names:
                    findings.append(self._invalid_reference("system_design", f"workflows[{workflow.name}].steps[{step.step_name}].capability", step.capability, "capability"))
        for dependency in system_design.module_dependencies:
            if dependency.from_module not in module_names:
                findings.append(self._invalid_reference("system_design", "module_dependencies.from_module", dependency.from_module, "module"))
            if dependency.to_module not in module_names:
                findings.append(self._invalid_reference("system_design", "module_dependencies.to_module", dependency.to_module, "module"))

        for relationship in data_schema.relationships:
            if relationship.from_entity not in schema_entity_names:
                findings.append(self._invalid_reference("data_schema", f"relationships[{relationship.name}].from_entity", relationship.from_entity, "schema entity"))
            if relationship.to_entity not in schema_entity_names:
                findings.append(self._invalid_reference("data_schema", f"relationships[{relationship.name}].to_entity", relationship.to_entity, "schema entity"))
        for constraint in data_schema.constraints:
            if constraint.entity not in schema_entity_names:
                findings.append(self._invalid_reference("data_schema", "constraints.entity", constraint.entity, "schema entity"))
        return findings

    def _invalid_reference(self, stage: str, related_field: str, missing_name: str, kind: str) -> ValidationFinding:
        """Build a single invalid_reference finding for a cross-reference that does not resolve."""
        return ValidationFinding(
            finding_id="",
            category="invalid_reference",
            severity="critical",
            stage=stage,  # type: ignore[arg-type]
            message=f"Reference to {kind} '{missing_name}' does not resolve to any defined {kind}.",
            related_field=related_field,
            recommendation=f"Regenerate the '{stage}' artifact; the {kind} '{missing_name}' must exist.",
        )

    def _check_orphan_relationships(
        self, intent_ir: IntentIR, data_schema: DataSchema
    ) -> tuple[list[ValidationFinding], int]:
        """Verify every IntentIR relationship has a corresponding SchemaRelationship, unless already acknowledged."""
        findings: list[ValidationFinding] = []
        acknowledged_gaps = 0
        schema_pairs = {
            (rel.from_entity, rel.to_entity, rel.source_relationship_type) for rel in data_schema.relationships
        }

        for relationship in intent_ir.relationships:
            key = (
                _to_snake_case(relationship.from_entity),
                _to_snake_case(relationship.to_entity),
                relationship.relationship_type,
            )
            if key in schema_pairs:
                continue

            is_acknowledged = any(
                relationship.from_entity in ambiguity.question and relationship.to_entity in ambiguity.question
                for ambiguity in data_schema.schema_ambiguities
            )
            if is_acknowledged:
                acknowledged_gaps += 1
                continue

            findings.append(
                ValidationFinding(
                    finding_id="",
                    category="orphan_relationship",
                    severity="error",
                    stage="data_schema",
                    message=f"IntentIR relationship '{relationship.from_entity}' -> '{relationship.to_entity}' "
                    f"({relationship.relationship_type}) has no corresponding SchemaRelationship and is "
                    "not explained by any reported schema ambiguity.",
                    related_field=f"relationships[{relationship.from_entity}->{relationship.to_entity}]",
                    recommendation="Re-run Schema Generation, or investigate why this relationship was dropped.",
                )
            )
        return findings, acknowledged_gaps

    def _check_risk_propagation(
        self, intent_ir: IntentIR, system_design: SystemDesign, data_schema: DataSchema
    ) -> list[ValidationFinding]:
        """Verify high/critical IntentIR risks reach SystemDesign, and SystemDesign risks reach DataSchema."""
        findings: list[ValidationFinding] = []
        design_risk_categories = {risk.category for risk in system_design.design_risks}

        for risk_flag in intent_ir.risk_flags:
            if risk_flag.severity not in rules.PROPAGATION_REQUIRED_SEVERITIES:
                continue
            if risk_flag.category not in design_risk_categories:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="risk_propagation_failure",
                        severity="error",
                        stage="system_design",
                        message=f"IntentIR risk_flag category '{risk_flag.category}' (severity="
                        f"'{risk_flag.severity}') has no corresponding SystemDesign design_risk.",
                        related_field="risk_flags",
                        recommendation="Re-run System Design so this risk is attributed to the affected modules.",
                    )
                )

        entity_module = {name: module.name for module in system_design.modules for name in module.owned_entities}
        module_to_schema_entities: dict[str, list[str]] = {}
        for entity in data_schema.entities:
            module_to_schema_entities.setdefault(entity.module, []).append(entity.name)
        constrained_entities = {(c.entity, c.constraint_type) for c in data_schema.constraints}

        for design_risk in system_design.design_risks:
            if design_risk.severity not in rules.PROPAGATION_REQUIRED_SEVERITIES:
                continue
            expected_constraint_type = rules.RISK_CONSTRAINT_TYPE_MAP.get(design_risk.category)
            if expected_constraint_type is None or not design_risk.affected_modules:
                continue
            candidate_entities = [
                name for module_name in design_risk.affected_modules for name in module_to_schema_entities.get(module_name, [])
            ]
            if candidate_entities and not any(
                (name, expected_constraint_type) in constrained_entities for name in candidate_entities
            ):
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="risk_propagation_failure",
                        severity="error",
                        stage="data_schema",
                        message=f"SystemDesign design_risk category '{design_risk.category}' (severity="
                        f"'{design_risk.severity}') produced no '{expected_constraint_type}' constraint "
                        f"in DataSchema for modules {design_risk.affected_modules}.",
                        related_field="constraints",
                        recommendation="Re-run Schema Generation so this risk produces the expected constraint.",
                    )
                )
        return findings

    def _check_missing_required_fields(self, intent_ir: IntentIR, data_schema: DataSchema) -> list[ValidationFinding]:
        """Verify every schema entity has exactly one primary key, nullability matches the IR, and FKs exist."""
        findings: list[ValidationFinding] = []
        entities_by_name = {entity.name: entity for entity in intent_ir.entities}

        for entity in data_schema.entities:
            primary_keys = [f for f in entity.fields if f.is_primary_key]
            if len(primary_keys) != 1:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="missing_required_field",
                        severity="critical",
                        stage="data_schema",
                        message=f"SchemaEntity '{entity.name}' has {len(primary_keys)} primary key fields; expected exactly 1.",
                        related_field=f"entities[{entity.name}].fields",
                        recommendation="Regenerate the DataSchema; every entity must have exactly one primary key.",
                    )
                )

            source_entity = entities_by_name.get(entity.source_entity)
            if source_entity is None:
                continue
            attributes_by_name = {a.name: a for a in source_entity.attributes}
            for field in entity.fields:
                attribute = attributes_by_name.get(field.source_attribute) if field.source_attribute else None
                if attribute is not None and attribute.is_optional != field.is_nullable:
                    findings.append(
                        ValidationFinding(
                            finding_id="",
                            category="missing_required_field",
                            severity="warning",
                            stage="data_schema",
                            message=f"SchemaField '{entity.name}.{field.name}' has is_nullable={field.is_nullable}, "
                            f"but IntentIR attribute '{attribute.name}' has is_optional={attribute.is_optional}.",
                            related_field=f"entities[{entity.name}].fields[{field.name}].is_nullable",
                            recommendation="Regenerate the DataSchema so nullability matches the IntentIR attribute.",
                        )
                    )

        for relationship in data_schema.relationships:
            if relationship.cardinality != "many_to_many" and relationship.foreign_key_field is None:
                findings.append(
                    ValidationFinding(
                        finding_id="",
                        category="missing_required_field",
                        severity="error",
                        stage="data_schema",
                        message=f"SchemaRelationship '{relationship.name}' has cardinality "
                        f"'{relationship.cardinality}' but no foreign_key_field.",
                        related_field=f"relationships[{relationship.name}].foreign_key_field",
                        recommendation="Regenerate the DataSchema; non-many-to-many relationships require a foreign key field.",
                    )
                )
        return findings

    def _compute_confidence(
        self,
        intent_ir: IntentIR,
        system_design: SystemDesign,
        data_schema: DataSchema,
        findings: list[ValidationFinding],
    ) -> float:
        """Cap confidence at the weakest upstream confidence, then subtract a penalty per finding severity."""
        confidence = min(intent_ir.confidence, system_design.confidence, data_schema.confidence)
        for finding in findings:
            confidence -= rules.CONFIDENCE_PENALTIES[finding.severity]
        return round(max(confidence, 0.0), 2)

    def _determine_decision(
        self,
        intent_ir: IntentIR,
        system_design: SystemDesign,
        data_schema: DataSchema,
        findings: list[ValidationFinding],
    ) -> tuple[PipelineDecision, ValidationStatus]:
        """Apply the strict severity ladder to decide whether the pipeline may proceed."""
        if intent_ir.status != "complete" or system_design.status != "complete" or data_schema.status != "complete":
            return "halt", "failed"
        if any(f.severity in ("critical", "error") for f in findings):
            return "halt", "failed"
        if any(f.severity == "warning" for f in findings):
            return "proceed_with_warnings", "passed_with_warnings"
        return "proceed", "passed"
