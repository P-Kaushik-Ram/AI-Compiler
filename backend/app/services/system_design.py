"""Deterministic, rule-based implementation of the System Design compiler stage.

This module converts a Stage 1 ``IntentIR`` into a ``SystemDesign`` without generating
any database schema, API, UI, or configuration — those belong to later stages. Stage 2
depends only on ``app.models.intent`` and ``app.models.system_design``; it does not import
anything from ``app.services.intent_extraction``, keeping it independently testable and
swappable.
"""
import uuid

from app.models.intent import Action, Entity, FunctionalRequirement, IntentIR, Relationship, RiskFlag
from app.models.system_design import (
    Actor,
    ArchitectureStyle,
    Capability,
    DesignAmbiguity,
    DesignRisk,
    ExternalDependency,
    ModuleDependency,
    ModuleRef,
    SystemDesign,
    SystemDesignStatus,
    Workflow,
    WorkflowStep,
)
from app.services import system_design_rules as rules

DESIGN_VERSION = "1.0"
GENERAL_MODULE_NAME = "General"


class SystemDesignService:
    """Builds a SystemDesign from an IntentIR using fixed, deterministic rules."""

    def build(self, intent_ir: IntentIR) -> SystemDesign:
        """Run the full System Design pipeline and return a complete SystemDesign."""
        if intent_ir.status != "complete":
            return self._build_rejected_design(intent_ir)

        entity_to_module, module_purposes = self._decompose_modules(intent_ir)
        actions_by_entity = self._group_actions_by_entity(intent_ir.actions)

        capabilities = self._build_capabilities(
            intent_ir.entities, actions_by_entity, entity_to_module, intent_ir.risk_flags
        )
        ambiguities: list[DesignAmbiguity] = []
        if any(c.module == GENERAL_MODULE_NAME for c in capabilities):
            ambiguities.append(
                DesignAmbiguity(
                    question="Some actions could not be mapped to a specific entity and were "
                    "grouped under a General module. Please confirm their intended owner.",
                    related_field="actions",
                    severity="advisory",
                )
            )

        modules = self._build_modules(entity_to_module, module_purposes, capabilities)
        entity_to_capability = self._build_entity_capability_map(capabilities, intent_ir.entities)

        workflows = self._build_workflows(intent_ir.functional_requirements, entity_to_capability)
        actors, actor_ambiguity = self._build_actors(intent_ir, capabilities)
        if actor_ambiguity is not None:
            ambiguities.append(actor_ambiguity)

        module_dependencies = self._build_module_dependencies(
            intent_ir, entity_to_module, workflows, capabilities
        )
        external_dependencies = self._build_external_dependencies(intent_ir, modules)
        design_risks = self._build_design_risks(intent_ir.risk_flags, modules, intent_ir.entities)

        status = self._determine_status(ambiguities)
        confidence = self._compute_confidence(ambiguities)
        architecture_style = self._determine_architecture_style(modules, module_dependencies)

        return SystemDesign(
            design_id=str(uuid.uuid4()),
            version=DESIGN_VERSION,
            source_intent_id=intent_ir.intent_id,
            architecture_style=architecture_style,
            modules=modules,
            capabilities=capabilities,
            workflows=workflows,
            actors=actors,
            module_dependencies=module_dependencies,
            external_dependencies=external_dependencies,
            design_ambiguities=ambiguities,
            design_risks=design_risks,
            confidence=confidence,
            status=status,
        )

    def _build_rejected_design(self, intent_ir: IntentIR) -> SystemDesign:
        """Build the fixed SystemDesign returned when the source IntentIR is not complete."""
        return SystemDesign(
            design_id=str(uuid.uuid4()),
            version=DESIGN_VERSION,
            source_intent_id=intent_ir.intent_id,
            architecture_style="single_module",
            confidence=0.0,
            status="rejected",
            design_ambiguities=[
                DesignAmbiguity(
                    question="Cannot perform System Design on an IntentIR with "
                    f"status='{intent_ir.status}'. Resolve Stage 1 ambiguities first.",
                    related_field="status",
                    severity="blocking",
                )
            ],
        )

    def _decompose_modules(self, intent_ir: IntentIR) -> tuple[dict[str, str], dict[str, str]]:
        """Assign every entity to exactly one module name via auth/risk isolation plus connected components."""
        entity_names = [e.name for e in intent_ir.entities]
        entity_to_module: dict[str, str] = {}
        module_purposes: dict[str, str] = {}

        auth_actions_present = any(a.name in rules.AUTH_ACTION_NAMES for a in intent_ir.actions)
        if rules.AUTH_ENTITY_NAME in entity_names and auth_actions_present:
            entity_to_module[rules.AUTH_ENTITY_NAME] = "Authentication"
            module_purposes["Authentication"] = "Account registration and authentication."

        risk_categories = {flag.category for flag in intent_ir.risk_flags}
        for category, candidates in rules.RISK_ISOLATION_ENTITIES.items():
            if category not in risk_categories:
                continue
            for candidate in candidates:
                if candidate in entity_names and candidate not in entity_to_module:
                    module_name = f"{candidate} Management"
                    entity_to_module[candidate] = module_name
                    module_purposes[module_name] = (
                        f"Isolated handling of {candidate} data due to an associated risk flag."
                    )

        remaining = [name for name in entity_names if name not in entity_to_module]
        components = self._connected_components(remaining, intent_ir.relationships)
        for component in components:
            module_name = (
                f"{component[0]} Management"
                if len(component) == 1
                else " & ".join(sorted(component)) + " Management"
            )
            for name in component:
                entity_to_module[name] = module_name
            module_purposes.setdefault(
                module_name, f"Owns and manages {', '.join(sorted(component))}."
            )

        return entity_to_module, module_purposes

    def _connected_components(self, names: list[str], relationships: list[Relationship]) -> list[list[str]]:
        """Group entity names into connected components using the IR's relationship edges."""
        name_set = set(names)
        adjacency: dict[str, set[str]] = {name: set() for name in names}
        for rel in relationships:
            if rel.from_entity in name_set and rel.to_entity in name_set:
                adjacency[rel.from_entity].add(rel.to_entity)
                adjacency[rel.to_entity].add(rel.from_entity)

        visited: set[str] = set()
        components: list[list[str]] = []
        for name in names:
            if name in visited:
                continue
            stack = [name]
            component: list[str] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                stack.extend(adjacency[current] - visited)
            components.append(sorted(component))
        return components

    def _group_actions_by_entity(self, actions: list[Action]) -> dict[str | None, list[Action]]:
        """Bucket actions by their target_entity, using None as the key for unowned actions."""
        grouped: dict[str | None, list[Action]] = {}
        for action in actions:
            grouped.setdefault(action.target_entity, []).append(action)
        return grouped

    def _build_capabilities(
        self,
        entities: list[Entity],
        actions_by_entity: dict[str | None, list[Action]],
        entity_to_module: dict[str, str],
        risk_flags: list[RiskFlag],
    ) -> list[Capability]:
        """Build one capability per entity that has actions, plus a catch-all for unowned actions."""
        capabilities: list[Capability] = []
        for entity in entities:
            entity_actions = actions_by_entity.get(entity.name, [])
            if not entity_actions:
                continue
            module_name = entity_to_module[entity.name]
            is_pure_auth = module_name == "Authentication" and all(
                a.name in rules.AUTH_ACTION_NAMES for a in entity_actions
            )
            name = "Account Access" if is_pure_auth else f"{entity.name} Management"
            capabilities.append(
                Capability(
                    name=name,
                    module=module_name,
                    description=f"Operations available for {entity.name}.",
                    related_actions=[a.name for a in entity_actions],
                    risk_level=self._capability_risk_level(entity, risk_flags),
                )
            )

        unowned_actions = actions_by_entity.get(None, [])
        if unowned_actions:
            capabilities.append(
                Capability(
                    name=GENERAL_MODULE_NAME,
                    module=GENERAL_MODULE_NAME,
                    description="Actions that could not be mapped to a specific entity.",
                    related_actions=[a.name for a in unowned_actions],
                    risk_level="none",
                )
            )
        return capabilities

    def _capability_risk_level(self, entity: Entity, risk_flags: list[RiskFlag]) -> str:
        """Roll up the highest applicable risk severity from the IR onto a single entity's capability."""
        best_rank = 0
        best_level = "none"
        attribute_names = {a.name for a in entity.attributes}
        for flag in risk_flags:
            affected_by_entity_map = entity.name in rules.RISK_AFFECTED_ENTITIES.get(flag.category, ())
            affected_by_pii = (
                flag.category in ("legal", "compliance", "security")
                and bool(attribute_names & rules.PII_ATTRIBUTE_NAMES)
            )
            if not (affected_by_entity_map or affected_by_pii):
                continue
            rank = rules.SEVERITY_RANK.get(flag.severity, 0)
            if rank > best_rank:
                best_rank = rank
                best_level = flag.severity
        return best_level

    def _build_modules(
        self,
        entity_to_module: dict[str, str],
        module_purposes: dict[str, str],
        capabilities: list[Capability],
    ) -> list[ModuleRef]:
        """Assemble ModuleRef records from the entity->module mapping and built capabilities."""
        owned_entities_by_module: dict[str, list[str]] = {}
        for entity_name, module_name in entity_to_module.items():
            owned_entities_by_module.setdefault(module_name, []).append(entity_name)

        capabilities_by_module: dict[str, list[str]] = {}
        for capability in capabilities:
            capabilities_by_module.setdefault(capability.module, []).append(capability.name)

        module_names = set(owned_entities_by_module) | set(capabilities_by_module)
        modules: list[ModuleRef] = []
        for module_name in module_names:
            owned_entities = sorted(owned_entities_by_module.get(module_name, []))
            capability_names = capabilities_by_module.get(module_name, [])
            source_fields = [f"entities[{name}]" for name in owned_entities] + [
                f"actions[{action}]"
                for cap in capabilities
                if cap.module == module_name
                for action in cap.related_actions
            ]
            purpose = module_purposes.get(
                module_name, "Handles actions that do not belong to a specific entity."
            )
            modules.append(
                ModuleRef(
                    name=module_name,
                    purpose=purpose,
                    owned_entities=owned_entities,
                    capabilities=capability_names,
                    source_fields=source_fields,
                )
            )

        modules.sort(key=lambda m: (m.name != "Authentication", m.name == GENERAL_MODULE_NAME, m.name))
        return modules

    def _build_entity_capability_map(
        self, capabilities: list[Capability], entities: list[Entity]
    ) -> dict[str, str]:
        """Map each entity name to the name of the capability that owns its actions, for workflow matching."""
        entity_names = {e.name for e in entities}
        mapping: dict[str, str] = {}
        for capability in capabilities:
            if capability.name == "Account Access":
                mapping[rules.AUTH_ENTITY_NAME] = capability.name
                continue
            for entity_name in entity_names:
                if capability.name == f"{entity_name} Management":
                    mapping[entity_name] = capability.name
        return mapping

    def _build_workflows(
        self,
        functional_requirements: list[FunctionalRequirement],
        entity_to_capability: dict[str, str],
    ) -> list[Workflow]:
        """Synthesize a linear workflow for each requirement containing sequencing language."""
        workflows: list[Workflow] = []
        for index, requirement in enumerate(functional_requirements, start=1):
            text = (requirement.source_phrase or requirement.description).lower()
            if not any(keyword in text for keyword in rules.SEQUENCING_KEYWORDS):
                continue

            ordered_capabilities = self._order_capabilities_by_mention(text, entity_to_capability)
            if len(ordered_capabilities) < 2:
                continue

            steps: list[WorkflowStep] = []
            for step_index, capability_name in enumerate(ordered_capabilities):
                step_name = f"Step {step_index + 1}: {capability_name}"
                depends_on = [steps[-1].step_name] if steps else []
                steps.append(WorkflowStep(step_name=step_name, capability=capability_name, depends_on=depends_on))

            workflows.append(
                Workflow(
                    name=f"Workflow {index}",
                    trigger=requirement.description,
                    steps=steps,
                    outcome=f"{ordered_capabilities[-1]} completed.",
                )
            )
        return workflows

    def _order_capabilities_by_mention(self, text: str, entity_to_capability: dict[str, str]) -> list[str]:
        """Return capability names for entities mentioned in text, ordered by first appearance."""
        hits = [
            (text.index(entity_name.lower()), capability_name)
            for entity_name, capability_name in entity_to_capability.items()
            if entity_name.lower() in text
        ]
        hits.sort(key=lambda pair: pair[0])
        ordered: list[str] = []
        for _, capability_name in hits:
            if capability_name not in ordered:
                ordered.append(capability_name)
        return ordered

    def _build_actors(
        self, intent_ir: IntentIR, capabilities: list[Capability]
    ) -> tuple[list[Actor], DesignAmbiguity | None]:
        """Build actors from the IR's user stories, or synthesize a generic one if none exist."""
        if not intent_ir.user_stories:
            if not intent_ir.entities:
                return [], None
            ambiguity = DesignAmbiguity(
                question="No user stories were present in the IntentIR; a generic 'User' actor "
                "was inferred from the system's entities.",
                related_field="actors",
                severity="advisory",
            )
            actor = Actor(
                name="User",
                description="Generic actor inferred from the system's entities.",
                accessible_capabilities=[c.name for c in capabilities],
                source_user_stories=[],
            )
            return [actor], ambiguity

        stories_by_actor: dict[str, list] = {}
        for story in intent_ir.user_stories:
            stories_by_actor.setdefault(story.actor, []).append(story)

        actors: list[Actor] = []
        for actor_name, stories in stories_by_actor.items():
            related_action_names = {s.related_action for s in stories if s.related_action}
            accessible = sorted(
                {
                    capability.name
                    for capability in capabilities
                    if related_action_names & set(capability.related_actions)
                }
            )
            actors.append(
                Actor(
                    name=actor_name,
                    description=f"An actor that performs: {', '.join(sorted(related_action_names)) or 'no specific actions'}.",
                    accessible_capabilities=accessible,
                    source_user_stories=[f"{s.actor}: {s.goal}" for s in stories],
                )
            )
        return actors, None

    def _build_module_dependencies(
        self,
        intent_ir: IntentIR,
        entity_to_module: dict[str, str],
        workflows: list[Workflow],
        capabilities: list[Capability],
    ) -> list[ModuleDependency]:
        """Derive data dependencies from IR relationships and workflow dependencies from step order."""
        dependencies: dict[tuple[str, str, str], ModuleDependency] = {}

        for rel in intent_ir.relationships:
            from_module = entity_to_module.get(rel.to_entity)
            to_module = entity_to_module.get(rel.from_entity)
            if not from_module or not to_module or from_module == to_module:
                continue
            key = (from_module, to_module, "data")
            if key not in dependencies:
                dependencies[key] = ModuleDependency(
                    from_module=from_module,
                    to_module=to_module,
                    dependency_type="data",
                    reason=f"'{rel.to_entity}' ({rel.relationship_type} relationship from "
                    f"'{rel.from_entity}') requires data owned by module '{to_module}'.",
                )

        capability_to_module = {c.name: c.module for c in capabilities}
        for workflow in workflows:
            for previous, current in zip(workflow.steps, workflow.steps[1:]):
                from_module = capability_to_module.get(current.capability)
                to_module = capability_to_module.get(previous.capability)
                if not from_module or not to_module or from_module == to_module:
                    continue
                key = (from_module, to_module, "workflow")
                if key not in dependencies:
                    dependencies[key] = ModuleDependency(
                        from_module=from_module,
                        to_module=to_module,
                        dependency_type="workflow",
                        reason=f"Workflow '{workflow.name}' requires step '{previous.step_name}' "
                        f"before '{current.step_name}'.",
                    )

        return list(dependencies.values())

    def _build_external_dependencies(
        self, intent_ir: IntentIR, modules: list[ModuleRef]
    ) -> list[ExternalDependency]:
        """Attach each IR integration to the module its purpose most plausibly belongs to."""
        if not intent_ir.integrations or not modules:
            return []

        module_by_owned_entity: dict[str, str] = {}
        for module in modules:
            for entity_name in module.owned_entities:
                module_by_owned_entity[entity_name] = module.name

        dependencies: list[ExternalDependency] = []
        for integration in intent_ir.integrations:
            purpose_lower = integration.purpose.lower()
            owning_module = modules[0].name
            if "payment" in purpose_lower:
                owning_module = (
                    module_by_owned_entity.get("Payment")
                    or module_by_owned_entity.get("Order")
                    or owning_module
                )
            elif any(kw in purpose_lower for kw in ("email", "messaging", "sms", "calendar")):
                owning_module = module_by_owned_entity.get("User", owning_module)
            dependencies.append(
                ExternalDependency(name=integration.name, purpose=integration.purpose, owning_module=owning_module)
            )
        return dependencies

    def _build_design_risks(
        self, risk_flags: list[RiskFlag], modules: list[ModuleRef], entities: list[Entity]
    ) -> list[DesignRisk]:
        """Propagate every IR risk flag into a DesignRisk, attributing it to the modules it affects."""
        design_risks: list[DesignRisk] = []
        entities_by_name = {e.name: e for e in entities}

        for flag in risk_flags:
            affected_entity_names = {
                name for name in rules.RISK_AFFECTED_ENTITIES.get(flag.category, ()) if name in entities_by_name
            }
            affected_modules = sorted(
                {m.name for m in modules if set(m.owned_entities) & affected_entity_names}
            )

            if not affected_modules and flag.category in ("legal", "compliance", "security"):
                affected_modules = sorted(
                    m.name
                    for m in modules
                    if any(
                        attribute_name in rules.PII_ATTRIBUTE_NAMES
                        for entity_name in m.owned_entities
                        for attribute_name in (a.name for a in entities_by_name[entity_name].attributes)
                    )
                )

            if not affected_modules and flag.severity in ("high", "critical"):
                affected_modules = sorted(m.name for m in modules)

            design_risks.append(
                DesignRisk(
                    category=flag.category,
                    description=flag.description,
                    severity=flag.severity,
                    affected_modules=affected_modules,
                    architectural_implication=rules.ARCHITECTURAL_IMPLICATIONS.get(
                        flag.category, rules.ARCHITECTURAL_IMPLICATIONS["other"]
                    ),
                )
            )
        return design_risks

    def _determine_status(self, ambiguities: list[DesignAmbiguity]) -> SystemDesignStatus:
        """Return 'needs_clarification' if any ambiguity is blocking, otherwise 'complete'."""
        if any(a.severity == "blocking" for a in ambiguities):
            return "needs_clarification"
        return "complete"

    def _compute_confidence(self, ambiguities: list[DesignAmbiguity]) -> float:
        """Start from a high baseline and subtract for each ambiguity surfaced during design."""
        confidence = 0.9
        for ambiguity in ambiguities:
            confidence -= 0.3 if ambiguity.severity == "blocking" else 0.1
        return round(max(confidence, 0.1), 2)

    def _determine_architecture_style(
        self, modules: list[ModuleRef], dependencies: list[ModuleDependency]
    ) -> ArchitectureStyle:
        """Classify the design as single_module or modular_monolith based on module count."""
        if len(modules) <= 1:
            return "single_module"
        return "modular_monolith"
