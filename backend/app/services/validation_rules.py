"""Static data driving the deterministic Validation & Repair service.

Separated from ``validation.py`` for the same reason as the prior stages' rule modules:
heuristics and thresholds can grow without touching the checking logic itself.
"""
from app.services.schema_generation_rules import RISK_CONSTRAINT_TYPE_MAP  # noqa: F401  (reused)

# Confidence deducted per finding, keyed by severity. "info" findings never reduce confidence.
CONFIDENCE_PENALTIES: dict[str, float] = {
    "critical": 0.30,
    "error": 0.15,
    "warning": 0.05,
    "info": 0.0,
}

# Upstream IntentIR/SystemDesign risk severities serious enough to require downstream propagation.
PROPAGATION_REQUIRED_SEVERITIES: frozenset[str] = frozenset({"high", "critical"})
