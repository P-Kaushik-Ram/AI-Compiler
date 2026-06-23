"""Static keyword and template data used by the deterministic Intent Extraction service.

Keeping this data separate from the extraction logic in ``intent_extraction.py`` lets the
rule set grow (or eventually be swapped for an LLM-backed extractor) without touching the
pipeline that consumes it.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AttributeTemplate:
    """A default attribute applied to an entity when no explicit fields are stated."""

    name: str
    type_hint: str
    is_optional: bool


@dataclass(frozen=True)
class EntityTemplate:
    """The canonical shape of an entity recognized by a keyword match."""

    canonical_name: str
    description: str
    attributes: tuple[AttributeTemplate, ...] = field(default_factory=tuple)


# Maps a lowercase singular keyword to the entity template it implies.
ENTITY_KEYWORDS: dict[str, EntityTemplate] = {
    "user": EntityTemplate(
        "User",
        "Registered account holder",
        (
            AttributeTemplate("email", "string", False),
            AttributeTemplate("password", "string", False),
        ),
    ),
    "contact": EntityTemplate(
        "Contact",
        "A person or organization tracked in the system",
        (
            AttributeTemplate("name", "string", False),
            AttributeTemplate("email", "string", True),
            AttributeTemplate("phone", "string", True),
        ),
    ),
    "lead": EntityTemplate(
        "Lead",
        "A prospective customer being tracked through a sales pipeline",
        (
            AttributeTemplate("name", "string", False),
            AttributeTemplate("status", "string", False),
        ),
    ),
    "customer": EntityTemplate(
        "Customer",
        "A person or organization that purchases from the system",
        (
            AttributeTemplate("name", "string", False),
            AttributeTemplate("email", "string", True),
        ),
    ),
    "order": EntityTemplate(
        "Order",
        "A purchase made by a customer",
        (
            AttributeTemplate("status", "string", False),
            AttributeTemplate("total", "number", False),
        ),
    ),
    "product": EntityTemplate(
        "Product",
        "An item available for sale",
        (
            AttributeTemplate("name", "string", False),
            AttributeTemplate("price", "number", False),
        ),
    ),
    "invoice": EntityTemplate(
        "Invoice",
        "A billing document issued to a customer",
        (
            AttributeTemplate("amount", "number", False),
            AttributeTemplate("due_date", "date", True),
        ),
    ),
    "payment": EntityTemplate(
        "Payment",
        "A record of funds transferred for an order or invoice",
        (
            AttributeTemplate("amount", "number", False),
            AttributeTemplate("method", "string", False),
        ),
    ),
    "todo": EntityTemplate(
        "Todo",
        "A task item owned by a user",
        (
            AttributeTemplate("title", "string", False),
            AttributeTemplate("description", "string", True),
            AttributeTemplate("due_date", "date", True),
            AttributeTemplate("completed", "boolean", False),
        ),
    ),
    "task": EntityTemplate(
        "Task",
        "A unit of work tracked by the system",
        (
            AttributeTemplate("title", "string", False),
            AttributeTemplate("completed", "boolean", False),
        ),
    ),
    "patient": EntityTemplate(
        "Patient",
        "An individual receiving medical care",
        (
            AttributeTemplate("name", "string", False),
            AttributeTemplate("date_of_birth", "date", True),
        ),
    ),
    "doctor": EntityTemplate(
        "Doctor",
        "A medical professional providing care",
        (AttributeTemplate("name", "string", False),),
    ),
    "appointment": EntityTemplate(
        "Appointment",
        "A scheduled meeting between a patient and a provider",
        (AttributeTemplate("scheduled_at", "datetime", False),),
    ),
    "student": EntityTemplate(
        "Student",
        "An individual enrolled in a course or program",
        (AttributeTemplate("name", "string", False),),
    ),
    "course": EntityTemplate(
        "Course",
        "An educational offering students enroll in",
        (AttributeTemplate("title", "string", False),),
    ),
    "post": EntityTemplate(
        "Post",
        "A piece of content shared by a user",
        (AttributeTemplate("content", "string", False),),
    ),
    "comment": EntityTemplate(
        "Comment",
        "A reply or remark left on a post",
        (AttributeTemplate("content", "string", False),),
    ),
}

# Maps a domain to the keywords that signal it, used for domain classification.
DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "crm": ("crm", "customer relationship", "contacts", "leads", "sales pipeline"),
    "ecommerce": ("ecommerce", "shop", "store", "cart", "checkout", "product", "order"),
    "healthcare": (
        "patient", "doctor", "medical", "health", "diagnosis", "clinic", "hospital", "prescription",
    ),
    "education": ("student", "course", "teacher", "school", "enrollment", "grade", "classroom"),
    "finance": ("invoice", "transaction", "bank", "loan", "accounting", "ledger"),
    "logistics": ("shipment", "delivery", "warehouse", "fleet", "logistics"),
    "social": ("post", "comment", "follow", "feed", "social network", "friend"),
    "productivity": ("todo", "task", "note", "reminder", "checklist"),
}

# Maps an integration keyword to its templated purpose.
INTEGRATION_KEYWORDS: dict[str, str] = {
    "stripe": "Payment processing",
    "paypal": "Payment processing",
    "sendgrid": "Email delivery",
    "mailchimp": "Email marketing",
    "twilio": "SMS/voice messaging",
    "slack": "Team messaging notifications",
    "google calendar": "Calendar scheduling",
    "zoom": "Video conferencing",
}

# Sentence-level keywords that mark a sentence as a functional requirement.
FUNCTIONAL_REQUIREMENT_KEYWORDS: tuple[str, ...] = (
    "only", "must", "cannot", "can't", "should", "require", "can only",
)

# Maps a non-functional requirement category to the keywords that signal it.
NON_FUNCTIONAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "performance": ("fast", "real-time", "realtime", "low latency", "performance"),
    "scalability": ("scale", "scalable", "high traffic", "thousands of users"),
    "availability": ("uptime", "available", "24/7", "always on"),
    "compliance": ("gdpr", "hipaa", "comply", "compliance"),
    "usability": ("easy to use", "intuitive", "user-friendly", "simple to use"),
}

# Maps a risk category to the keywords that signal it.
RISK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "payments": ("payment", "credit card", "card number", "checkout", "billing", "stripe", "paypal"),
    "medical_data": ("patient", "medical", "health record", "diagnosis", "prescription"),
    "legal": ("ssn", "social security", "legal", "contract"),
    "compliance": ("gdpr", "hipaa", "pci", "compliance"),
    "security": ("sensitive", "encrypt", "pii", "personal data", "security"),
}

AUTH_KEYWORDS: tuple[str, ...] = ("sign up", "signup", "register", "log in", "login")
AUTH_NEGATION_PHRASES: tuple[str, ...] = ("no login", "no auth", "without login", "without auth")
OWNERSHIP_PHRASES: tuple[str, ...] = ("their own", "my own", "user's own", "users own")
MANAGE_KEYWORDS: tuple[str, ...] = ("manage",)
CREATE_KEYWORDS: tuple[str, ...] = ("create", "add")
UPDATE_KEYWORDS: tuple[str, ...] = ("update", "edit")
DELETE_KEYWORDS: tuple[str, ...] = ("delete", "remove")
LIST_KEYWORDS: tuple[str, ...] = ("list", "view", "see")
