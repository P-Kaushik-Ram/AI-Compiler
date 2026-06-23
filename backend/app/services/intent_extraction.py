"""Deterministic, rule-based implementation of the Intent Extraction compiler stage.

This module converts a raw natural-language prompt into a validated ``IntentIR``
without calling any external LLM. It exists so the Intent Extraction stage has a
working, testable baseline; a future revision may swap this implementation for an
LLM-backed one behind the same ``IntentExtractionService.extract`` interface.
"""
import re
import uuid

from app.models.intent import (
    Action,
    Ambiguity,
    Assumption,
    Attribute,
    DomainType,
    Entity,
    FunctionalRequirement,
    Integration,
    IntentIR,
    NonFunctionalRequirement,
    Relationship,
    RiskFlag,
    StatusType,
    UserStory,
)
from app.services import intent_rules as rules

IR_VERSION = "1.0"


def _normalize(text: str) -> str:
    """Lowercase the prompt and strip hyphens so hyphenated and non-hyphenated forms match."""
    return text.lower().replace("-", "")


def _keyword_present(normalized_text: str, keyword: str) -> bool:
    """Return True if ``keyword`` (singular or simple plural) occurs in ``normalized_text``."""
    if " " in keyword:
        return keyword in normalized_text
    pattern = rf"\b{re.escape(keyword)}(?:es|s)?\b"
    return re.search(pattern, normalized_text) is not None


def _split_sentences(text: str) -> list[str]:
    """Split a prompt into trimmed sentences for sentence-level requirement detection."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


class IntentExtractionService:
    """Extracts a structured ``IntentIR`` from a raw natural-language prompt using fixed rules."""

    def extract(self, raw_prompt: str) -> IntentIR:
        """Run the full extraction pipeline and return a complete, validated ``IntentIR``."""
        if not raw_prompt or not raw_prompt.strip():
            return self._build_rejected_ir(raw_prompt or "")

        normalized = _normalize(raw_prompt)
        sentences = _split_sentences(raw_prompt)

        domain = self._detect_domain(normalized)
        entities = self._find_entities(normalized)
        auth_detected = any(_keyword_present(normalized, kw) for kw in rules.AUTH_KEYWORDS)

        assumptions: list[Assumption] = self._build_attribute_assumptions(entities)

        if auth_detected and not any(entity.name == "User" for entity in entities):
            user_template = rules.ENTITY_KEYWORDS["user"]
            entities.append(
                Entity(
                    name=user_template.canonical_name,
                    description=user_template.description,
                    attributes=[
                        Attribute(name=a.name, type_hint=a.type_hint, is_optional=a.is_optional)
                        for a in user_template.attributes
                    ],
                    confidence=0.7,
                )
            )
            assumptions.append(
                Assumption(
                    description="Added an implicit 'User' entity because authentication "
                    "language was detected.",
                    rationale="The prompt mentions signing up or logging in but never "
                    "names the account-holding entity directly.",
                    affected_field="entities",
                )
            )

        actions, action_assumptions = self._find_actions(normalized, entities, auth_detected)
        assumptions.extend(action_assumptions)

        relationships = self._find_relationships(entities, actions, normalized)
        user_stories = self._build_user_stories(actions)
        functional_requirements = self._find_functional_requirements(sentences)
        non_functional_requirements = self._find_non_functional_requirements(
            sentences, normalized, auth_detected
        )
        integrations = self._find_integrations(normalized)
        risk_flags = self._find_risk_flags(normalized, domain, entities)
        ambiguities = self._find_ambiguities(normalized, entities, actions, domain)

        status = self._determine_status(ambiguities)
        confidence = self._compute_confidence(entities, actions, ambiguities)

        return IntentIR(
            intent_id=str(uuid.uuid4()),
            version=IR_VERSION,
            domain=domain,
            primary_intent=self._build_primary_intent(domain, entities, auth_detected),
            domain_summary=self._build_domain_summary(domain, entities),
            entities=entities,
            relationships=relationships,
            actions=actions,
            user_stories=user_stories,
            functional_requirements=functional_requirements,
            non_functional_requirements=non_functional_requirements,
            integrations=integrations,
            risk_flags=risk_flags,
            ambiguities=ambiguities,
            assumptions=assumptions,
            confidence=confidence,
            status=status,
            raw_prompt=raw_prompt,
        )

    def _build_rejected_ir(self, raw_prompt: str) -> IntentIR:
        """Build the fixed IR returned when the prompt is empty or whitespace-only."""
        return IntentIR(
            intent_id=str(uuid.uuid4()),
            version=IR_VERSION,
            domain="general",
            primary_intent="unknown",
            domain_summary="No input provided.",
            confidence=0.0,
            status="rejected",
            raw_prompt=raw_prompt,
            ambiguities=[
                Ambiguity(
                    question="The prompt is empty. Please describe what system you want to build.",
                    related_field="raw_prompt",
                    severity="blocking",
                )
            ],
        )

    def _detect_domain(self, normalized: str) -> DomainType:
        """Classify the prompt into a domain by counting keyword hits per known domain."""
        best_domain: DomainType = "general"
        best_score = 0
        for domain, keywords in rules.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if _keyword_present(normalized, kw))
            if score > best_score:
                best_score = score
                best_domain = domain  # type: ignore[assignment]
        return best_domain

    def _find_entities(self, normalized: str) -> list[Entity]:
        """Match known entity keywords in the prompt and build their default-attribute Entity."""
        entities: list[Entity] = []
        seen_names: set[str] = set()
        for keyword, template in rules.ENTITY_KEYWORDS.items():
            if not _keyword_present(normalized, keyword):
                continue
            if template.canonical_name in seen_names:
                continue
            seen_names.add(template.canonical_name)
            entities.append(
                Entity(
                    name=template.canonical_name,
                    description=template.description,
                    attributes=[
                        Attribute(name=a.name, type_hint=a.type_hint, is_optional=a.is_optional)
                        for a in template.attributes
                    ],
                    confidence=0.9,
                )
            )
        return entities

    def _build_attribute_assumptions(self, entities: list[Entity]) -> list[Assumption]:
        """Record one assumption per entity whose attributes came entirely from a template."""
        return [
            Assumption(
                description=f"Assumed default attributes for '{entity.name}' based on common "
                "patterns since the prompt did not specify fields explicitly.",
                rationale="No explicit field list was given for this entity.",
                affected_field=f"entities[{entity.name}].attributes",
            )
            for entity in entities
            if entity.attributes
        ]

    def _find_actions(
        self, normalized: str, entities: list[Entity], auth_detected: bool
    ) -> tuple[list[Action], list[Assumption]]:
        """Derive actions from auth keywords, the CRUD-implying 'manage', and explicit verbs."""
        actions: list[Action] = []
        assumptions: list[Assumption] = []
        entity_names = [e.name for e in entities]

        if _keyword_present(normalized, "sign up") or _keyword_present(normalized, "register"):
            actions.append(
                Action(name="sign_up", target_entity="User", description="Register a new account", confidence=0.9)
            )
        if _keyword_present(normalized, "log in") or _keyword_present(normalized, "login"):
            actions.append(
                Action(
                    name="log_in",
                    target_entity="User",
                    description="Authenticate an existing user",
                    confidence=0.9,
                )
            )

        manageable_entities = [name for name in entity_names if name != "User"]
        if _keyword_present(normalized, "manage") and manageable_entities:
            for name in manageable_entities:
                actions.extend(self._build_crud_actions(name))
            assumptions.append(
                Assumption(
                    description="Assumed full create/read/update/delete capability for "
                    f"{', '.join(manageable_entities)}.",
                    rationale="The word 'manage' implies complete CRUD capability unless stated otherwise.",
                    affected_field="actions",
                )
            )
        else:
            verb_groups = (
                (rules.CREATE_KEYWORDS, "create", "Create a new {entity}"),
                (rules.UPDATE_KEYWORDS, "update", "Edit an existing {entity}"),
                (rules.DELETE_KEYWORDS, "delete", "Remove a {entity}"),
                (rules.LIST_KEYWORDS, "list", "View existing {entity} records"),
            )
            for keywords, verb, description_template in verb_groups:
                if not any(_keyword_present(normalized, kw) for kw in keywords):
                    continue
                for name in manageable_entities:
                    actions.append(
                        Action(
                            name=f"{verb}_{name.lower()}",
                            target_entity=name,
                            description=description_template.format(entity=name),
                            confidence=0.75,
                        )
                    )

        if auth_detected:
            assumptions.append(
                Assumption(
                    description="Assumed standard email+password authentication; no specific "
                    "provider was mentioned.",
                    rationale="The prompt references signing up or logging in without naming an auth provider.",
                    affected_field="actions",
                )
            )

        return actions, assumptions

    def _build_crud_actions(self, entity_name: str) -> list[Action]:
        """Build the four standard create/read/update/delete actions for a single entity."""
        lower = entity_name.lower()
        return [
            Action(name=f"create_{lower}", target_entity=entity_name, description=f"Add a new {entity_name}", confidence=0.85),
            Action(name=f"update_{lower}", target_entity=entity_name, description=f"Edit an existing {entity_name}", confidence=0.85),
            Action(name=f"delete_{lower}", target_entity=entity_name, description=f"Remove a {entity_name}", confidence=0.85),
            Action(name=f"list_{lower}", target_entity=entity_name, description=f"View existing {entity_name} records", confidence=0.85),
        ]

    def _find_relationships(
        self, entities: list[Entity], actions: list[Action], normalized: str
    ) -> list[Relationship]:
        """Link User to every other entity it acts upon, using 'owns' when ownership language is present."""
        entity_names = {e.name for e in entities}
        if "User" not in entity_names:
            return []

        ownership_language = any(_keyword_present(normalized, phrase) for phrase in rules.OWNERSHIP_PHRASES)
        relationship_type = "owns" if ownership_language else "has_many"

        targets = {a.target_entity for a in actions if a.target_entity and a.target_entity != "User"}
        return [
            Relationship(
                from_entity="User",
                to_entity=target,
                relationship_type=relationship_type,  # type: ignore[arg-type]
                description=f"User {'owns' if ownership_language else 'manages'} {target} records.",
            )
            for target in sorted(targets)
        ]

    def _build_user_stories(self, actions: list[Action]) -> list[UserStory]:
        """Translate each action into a generic 'User wants to <action>' must-have story."""
        return [
            UserStory(
                actor="User",
                goal=action.description.rstrip("."),
                priority="must_have",
                related_action=action.name,
            )
            for action in actions
        ]

    def _find_functional_requirements(self, sentences: list[str]) -> list[FunctionalRequirement]:
        """Flag sentences containing business-rule language (only/must/cannot/should/require)."""
        requirements: list[FunctionalRequirement] = []
        for sentence in sentences:
            lowered = sentence.lower()
            if any(kw in lowered for kw in rules.FUNCTIONAL_REQUIREMENT_KEYWORDS):
                requirements.append(FunctionalRequirement(description=sentence, source_phrase=sentence))
        return requirements

    def _find_non_functional_requirements(
        self, sentences: list[str], normalized: str, auth_detected: bool
    ) -> list[NonFunctionalRequirement]:
        """Detect quality-attribute keywords (performance, compliance, etc.) and, separately, auth posture."""
        requirements: list[NonFunctionalRequirement] = []
        seen_categories: set[str] = set()
        for sentence in sentences:
            lowered = sentence.lower()
            for category, keywords in rules.NON_FUNCTIONAL_KEYWORDS.items():
                if category in seen_categories:
                    continue
                if any(kw in lowered for kw in keywords):
                    seen_categories.add(category)
                    requirements.append(
                        NonFunctionalRequirement(
                            category=category,  # type: ignore[arg-type]
                            description=sentence,
                            source_phrase=sentence,
                        )
                    )
        if auth_detected:
            requirements.append(
                NonFunctionalRequirement(
                    category="auth",
                    description="Users must authenticate to access the system.",
                )
            )
        return requirements

    def _find_integrations(self, normalized: str) -> list[Integration]:
        """Match known third-party service keywords and attach their templated purpose."""
        return [
            Integration(name=name, purpose=purpose)
            for name, purpose in rules.INTEGRATION_KEYWORDS.items()
            if _keyword_present(normalized, name)
        ]

    def _find_risk_flags(
        self, normalized: str, domain: DomainType, entities: list[Entity]
    ) -> list[RiskFlag]:
        """Flag payment, medical, legal, compliance, security, and high-ambiguity signals."""
        flags: list[RiskFlag] = []
        for category, keywords in rules.RISK_KEYWORDS.items():
            matched = next((kw for kw in keywords if _keyword_present(normalized, kw)), None)
            if matched is None:
                continue
            flags.append(
                RiskFlag(
                    category=category,  # type: ignore[arg-type]
                    description=f"Prompt references '{matched}', which may require special handling.",
                    severity="high" if category in ("medical_data", "compliance", "legal") else "medium",
                    source_phrase=matched,
                    recommended_handling=self._risk_handling_hint(category),
                )
            )

        if domain == "healthcare" and not any(f.category == "medical_data" for f in flags):
            flags.append(
                RiskFlag(
                    category="medical_data",
                    description="Domain was classified as healthcare; treat all entity data as potentially sensitive.",
                    severity="high",
                    recommended_handling=self._risk_handling_hint("medical_data"),
                )
            )

        if not entities:
            flags.append(
                RiskFlag(
                    category="high_ambiguity",
                    description="No entities could be identified from the prompt.",
                    severity="medium",
                    recommended_handling="Recommend requesting clarification before proceeding to System Design.",
                )
            )
        return flags

    def _risk_handling_hint(self, category: str) -> str:
        """Return a short, fixed downstream-handling recommendation for a risk category."""
        hints = {
            "payments": "Route to a PCI-aware schema and runtime review before implementation.",
            "medical_data": "Requires HIPAA-aware schema design and data encryption review.",
            "legal": "Recommend legal/compliance review before finalizing requirements.",
            "compliance": "Recommend a dedicated compliance review pass before Schema Generation.",
            "security": "Recommend a security review of authentication and data handling.",
        }
        return hints.get(category, "Recommend manual review before proceeding.")

    def _find_ambiguities(
        self, normalized: str, entities: list[Entity], actions: list[Action], domain: DomainType
    ) -> list[Ambiguity]:
        """Flag missing-scope, low domain-confidence, and conflicting-auth-statement ambiguities."""
        ambiguities: list[Ambiguity] = []

        if not entities and not actions:
            ambiguities.append(
                Ambiguity(
                    question="What should this system manage? Please specify the main entities "
                    "or data this system should handle.",
                    related_field="entities",
                    severity="blocking",
                )
            )

        if entities and domain == "general":
            ambiguities.append(
                Ambiguity(
                    question="The domain of this system is unclear — could you confirm the "
                    "industry/domain (e.g., CRM, e-commerce, healthcare)?",
                    related_field="domain",
                    severity="advisory",
                )
            )

        has_negation = any(_keyword_present(normalized, phrase) for phrase in rules.AUTH_NEGATION_PHRASES)
        has_auth = any(_keyword_present(normalized, kw) for kw in rules.AUTH_KEYWORDS)
        if has_negation and has_auth:
            ambiguities.append(
                Ambiguity(
                    question="The prompt both rejects and requires authentication — which is correct?",
                    related_field="non_functional_requirements",
                    severity="blocking",
                )
            )

        return ambiguities

    def _determine_status(self, ambiguities: list[Ambiguity]) -> StatusType:
        """Return 'needs_clarification' if any ambiguity is blocking, otherwise 'complete'."""
        if any(a.severity == "blocking" for a in ambiguities):
            return "needs_clarification"
        return "complete"

    def _compute_confidence(
        self, entities: list[Entity], actions: list[Action], ambiguities: list[Ambiguity]
    ) -> float:
        """Start from a high baseline and subtract for each ambiguity and missing structure."""
        if not entities and not actions:
            return 0.1
        confidence = 0.95
        for ambiguity in ambiguities:
            confidence -= 0.4 if ambiguity.severity == "blocking" else 0.1
        return round(max(confidence, 0.05), 2)

    def _build_primary_intent(self, domain: DomainType, entities: list[Entity], auth_detected: bool) -> str:
        """Compose a short snake_case label summarizing the system to be built."""
        parts = ["build", domain if (domain != "general" and entities) else "app"]
        if auth_detected:
            parts.append("with_auth")
        return "_".join(parts)

    def _build_domain_summary(self, domain: DomainType, entities: list[Entity]) -> str:
        """Compose a one-line human-readable restatement of what the system is about."""
        if not entities:
            return "Unable to determine the system's purpose from the prompt."
        entity_names = ", ".join(e.name for e in entities)
        domain_label = domain if domain != "general" else "general-purpose"
        return f"A {domain_label} system involving {entity_names}."
