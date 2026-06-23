"""Static data driving the deterministic System Design service.

Separated from ``system_design.py`` for the same reason as ``intent_rules.py``: the
heuristics here (which entity is "the" auth entity, which risk categories force module
isolation, which keywords imply step ordering) may need to grow or be tuned without
touching the transformation pipeline itself.
"""

AUTH_ENTITY_NAME = "User"
AUTH_ACTION_NAMES: tuple[str, ...] = ("sign_up", "log_in")

# Risk categories that force their associated entity into its own isolated module,
# even if it would otherwise be grouped with related entities.
RISK_ISOLATION_ENTITIES: dict[str, tuple[str, ...]] = {
    "payments": ("Payment",),
    "medical_data": ("Patient",),
}

# Entities considered directly affected by a given risk category, for rolling risk
# severity up onto capabilities and for attributing a DesignRisk to specific modules.
RISK_AFFECTED_ENTITIES: dict[str, tuple[str, ...]] = {
    "payments": ("Payment", "Order", "Invoice"),
    "medical_data": ("Patient", "Doctor", "Appointment"),
}

# Attribute names treated as personally identifiable, used to attribute legal/
# compliance/security risk flags to the modules that hold such data.
PII_ATTRIBUTE_NAMES: frozenset[str] = frozenset({"email", "password", "phone", "date_of_birth", "ssn"})

ARCHITECTURAL_IMPLICATIONS: dict[str, str] = {
    "payments": "Isolate payment-handling capability into its own module to minimize PCI compliance scope.",
    "medical_data": "Isolate patient-data capability and restrict access to satisfy HIPAA-style handling requirements.",
    "legal": "Flag affected modules for legal review before implementation.",
    "compliance": "Apply data-protection controls (e.g. consent/retention rules) to affected modules.",
    "security": "Apply restricted access and audit logging to affected modules.",
    "high_ambiguity": "Re-run Intent Extraction or request clarification before finalizing affected modules.",
    "other": "Flag for manual architectural review.",
}

SEVERITY_RANK: dict[str, int] = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# Keywords that signal a functional requirement encodes a step ordering constraint.
SEQUENCING_KEYWORDS: tuple[str, ...] = ("only after", "before", "once", "then", "must complete", "first")
