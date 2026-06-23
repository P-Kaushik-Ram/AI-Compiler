/** Mirrors backend/app/models/intent.py */

export type DomainType =
  | "crm"
  | "ecommerce"
  | "healthcare"
  | "education"
  | "finance"
  | "logistics"
  | "social"
  | "productivity"
  | "general"
  | "other";

export type StatusType = "complete" | "needs_clarification" | "rejected";
export type Severity = "low" | "medium" | "high" | "critical";
export type AmbiguitySeverity = "blocking" | "advisory";

export interface Attribute {
  name: string;
  type_hint: string;
  is_optional: boolean;
  source_phrase: string | null;
}

export interface Entity {
  name: string;
  description: string;
  attributes: Attribute[];
  confidence: number;
}

export type RelationshipType = "owns" | "has_many" | "has_one" | "belongs_to" | "associated_with";

export interface Relationship {
  from_entity: string;
  to_entity: string;
  relationship_type: RelationshipType;
  description: string;
  source_phrase: string | null;
}

export interface Action {
  name: string;
  target_entity: string | null;
  description: string;
  confidence: number;
}

export type UserStoryPriority = "must_have" | "should_have" | "nice_to_have";

export interface UserStory {
  actor: string;
  goal: string;
  priority: UserStoryPriority;
  related_action: string | null;
}

export interface FunctionalRequirement {
  description: string;
  related_entity: string | null;
  related_action: string | null;
  source_phrase: string | null;
}

export type NonFunctionalCategory =
  | "performance"
  | "scalability"
  | "availability"
  | "auth"
  | "compliance"
  | "usability"
  | "other";

export interface NonFunctionalRequirement {
  category: NonFunctionalCategory;
  description: string;
  source_phrase: string | null;
}

export interface Integration {
  name: string;
  purpose: string;
}

export type RiskCategory =
  | "compliance"
  | "payments"
  | "medical_data"
  | "legal"
  | "security"
  | "high_ambiguity"
  | "other";

export interface RiskFlag {
  category: RiskCategory;
  description: string;
  severity: Severity;
  source_phrase: string | null;
  recommended_handling: string | null;
}

export interface Ambiguity {
  question: string;
  related_field: string | null;
  severity: AmbiguitySeverity;
}

export interface Assumption {
  description: string;
  rationale: string;
  affected_field: string | null;
}

export interface IntentIR {
  intent_id: string;
  version: string;
  domain: DomainType;
  primary_intent: string;
  domain_summary: string;
  entities: Entity[];
  relationships: Relationship[];
  actions: Action[];
  user_stories: UserStory[];
  functional_requirements: FunctionalRequirement[];
  non_functional_requirements: NonFunctionalRequirement[];
  integrations: Integration[];
  risk_flags: RiskFlag[];
  ambiguities: Ambiguity[];
  assumptions: Assumption[];
  confidence: number;
  status: StatusType;
  raw_prompt: string;
}
