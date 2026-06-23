/** Mirrors backend/app/models/system_design.py */
import type { RiskCategory, Severity } from "./intent";

export type ArchitectureStyle = "modular_monolith" | "service_oriented" | "single_module";
export type SystemDesignStatus = "complete" | "needs_clarification" | "rejected";
export type DesignAmbiguitySeverity = "blocking" | "advisory";

export interface ModuleRef {
  name: string;
  purpose: string;
  owned_entities: string[];
  capabilities: string[];
  source_fields: string[];
}

export type CapabilityRiskLevel = "none" | "low" | "medium" | "high" | "critical";

export interface Capability {
  name: string;
  module: string;
  description: string;
  related_actions: string[];
  risk_level: CapabilityRiskLevel;
}

export interface WorkflowStep {
  step_name: string;
  capability: string;
  depends_on: string[];
}

export interface Workflow {
  name: string;
  trigger: string;
  steps: WorkflowStep[];
  outcome: string;
}

export interface Actor {
  name: string;
  description: string;
  accessible_capabilities: string[];
  source_user_stories: string[];
}

export type ModuleDependencyType = "data" | "workflow" | "integration";

export interface ModuleDependency {
  from_module: string;
  to_module: string;
  dependency_type: ModuleDependencyType;
  reason: string;
}

export interface ExternalDependency {
  name: string;
  purpose: string;
  owning_module: string;
}

export interface DesignAmbiguity {
  question: string;
  related_field: string | null;
  severity: DesignAmbiguitySeverity;
}

export interface DesignRisk {
  category: RiskCategory;
  description: string;
  severity: Severity;
  affected_modules: string[];
  architectural_implication: string;
}

export interface SystemDesign {
  design_id: string;
  version: string;
  source_intent_id: string;
  architecture_style: ArchitectureStyle;
  modules: ModuleRef[];
  capabilities: Capability[];
  workflows: Workflow[];
  actors: Actor[];
  module_dependencies: ModuleDependency[];
  external_dependencies: ExternalDependency[];
  design_ambiguities: DesignAmbiguity[];
  design_risks: DesignRisk[];
  confidence: number;
  status: SystemDesignStatus;
}
