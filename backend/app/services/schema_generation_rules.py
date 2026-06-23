"""Static data driving the deterministic Schema Generation service.

Separated from ``schema_generation.py`` for the same reason as the prior stages' rule
modules: heuristics can grow without touching the transformation pipeline itself.
"""
from app.services.system_design_rules import PII_ATTRIBUTE_NAMES  # noqa: F401  (re-exported for reuse)

# Maps an IntentIR attribute type_hint to a concrete schema data type.
TYPE_HINT_MAP: dict[str, str] = {
    "string": "string",
    "number": "float",
    "boolean": "boolean",
    "date": "date",
    "datetime": "datetime",
}
DEFAULT_DATA_TYPE = "string"

# Attribute names treated as naturally unique within their entity.
UNIQUE_FIELD_NAMES: frozenset[str] = frozenset({"email"})

# Maps an IntentIR relationship_type to (cardinality, swap_parent_and_child).
# When swap is True, to_entity is the "one"/parent side and from_entity is the "many"/child side.
RELATIONSHIP_CARDINALITY_MAP: dict[str, tuple[str, bool]] = {
    "owns": ("one_to_many", False),
    "has_many": ("one_to_many", False),
    "has_one": ("one_to_one", False),
    "belongs_to": ("one_to_many", True),
    "associated_with": ("many_to_many", False),
}

# Risk categories considered sensitive enough to mark a field as sensitive.
SENSITIVE_RISK_CATEGORIES: frozenset[str] = frozenset({"payments", "medical_data", "security"})

# Maps a risk category to the SchemaConstraint type it produces.
RISK_CONSTRAINT_TYPE_MAP: dict[str, str] = {
    "payments": "requires_encryption",
    "medical_data": "requires_encryption",
    "security": "requires_encryption",
    "compliance": "requires_audit_log",
    "legal": "requires_audit_log",
}

# Risk severities that warrant generating a SchemaConstraint.
CONSTRAINT_TRIGGER_SEVERITIES: frozenset[str] = frozenset({"high", "critical"})
