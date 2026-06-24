import type { BenchmarkPreset } from "../store/evaluationStore";
import type { DatasetCase } from "../types/evaluation";

export interface EvaluationPresetDefinition {
  id: Exclude<BenchmarkPreset, "custom">;
  label: string;
  description: string;
  datasetName: string;
  cases: DatasetCase[];
}

function makeCase(caseId: string, prompt: string, category: string): DatasetCase {
  return { case_id: caseId, prompt, category, expectation: null };
}

/** Built-in benchmark datasets. Wording matches the deterministic extractor's keyword rules
 * (see backend/app/services/intent_rules.py) and deliberately includes one vague prompt per
 * preset so success_rate/halt_rate aren't trivially 100%. */
export const EVALUATION_PRESETS: EvaluationPresetDefinition[] = [
  {
    id: "crm",
    label: "CRM Benchmark",
    description: "4 CRM prompts, including one too vague to compile.",
    datasetName: "crm-preset",
    cases: [
      makeCase(
        "crm-1",
        "Build a CRM where users can sign up, log in, and manage their own contacts and leads through a sales pipeline.",
        "crm"
      ),
      makeCase(
        "crm-2",
        "Build a CRM with contacts, leads, and deals. Sales reps should only see their own leads.",
        "crm"
      ),
      makeCase(
        "crm-3",
        "Build a CRM that integrates with Mailchimp for email campaigns targeting leads.",
        "crm"
      ),
      makeCase("crm-4", "Build a CRM.", "crm"),
    ],
  },
  {
    id: "mixed",
    label: "Mixed Domains",
    description: "5 prompts spanning e-commerce, productivity, social, and finance.",
    datasetName: "mixed-preset",
    cases: [
      makeCase(
        "mixed-1",
        "Build an e-commerce store where customers can browse products, add items to a cart, and checkout. Payments are processed through Stripe.",
        "ecommerce"
      ),
      makeCase(
        "mixed-2",
        "Build a todo app where users can sign up, log in, and manage their own tasks.",
        "productivity"
      ),
      makeCase(
        "mixed-3",
        "Build a social app where users can create posts and comment on other users' posts.",
        "social"
      ),
      makeCase(
        "mixed-4",
        "Build an invoicing system where accountants can manage invoices and track payments.",
        "finance"
      ),
      makeCase("mixed-5", "Build something useful for my business.", "vague"),
    ],
  },
  {
    id: "healthcare",
    label: "Healthcare Benchmark",
    description: "4 healthcare prompts, including one too vague to compile.",
    datasetName: "healthcare-preset",
    cases: [
      makeCase(
        "health-1",
        "Build a healthcare system where doctors can manage patients and schedule appointments. " +
          "Patient medical records must be encrypted and HIPAA compliant.",
        "healthcare"
      ),
      makeCase(
        "health-2",
        "Build a clinic system where patients can book appointments with doctors online.",
        "healthcare"
      ),
      makeCase(
        "health-3",
        "Build a hospital system managing patient diagnosis and prescription records, fully HIPAA compliant.",
        "healthcare"
      ),
      makeCase("health-4", "Build a healthcare app.", "healthcare"),
    ],
  },
];

export function getPreset(id: Exclude<BenchmarkPreset, "custom">): EvaluationPresetDefinition {
  const preset = EVALUATION_PRESETS.find((candidate) => candidate.id === id);
  if (!preset) {
    throw new Error(`Unknown evaluation preset: ${id}`);
  }
  return preset;
}

/** Parses the custom-dataset textarea (one prompt per line) into DatasetCase objects. */
export function parseCustomDataset(input: string): DatasetCase[] {
  return input
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((prompt, index) => makeCase(`custom-${index + 1}`, prompt, "custom"));
}
