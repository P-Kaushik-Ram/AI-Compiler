import { GraduationCap, HeartPulse, ListChecks, ShoppingCart, Users, type LucideIcon } from "lucide-react";

export interface PromptExample {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  prompt: string;
}

/** Quick-start prompts. Wording deliberately matches the deterministic extractor's keyword
 * rules (see backend/app/services/intent_rules.py) so each card produces a rich IntentIR. */
export const PROMPT_EXAMPLES: PromptExample[] = [
  {
    id: "crm",
    title: "CRM System",
    description: "Track contacts and leads through a sales pipeline.",
    icon: Users,
    prompt:
      "Build a CRM where users can sign up, log in, and manage their own contacts and leads " +
      "through a sales pipeline.",
  },
  {
    id: "todo",
    title: "Todo Application",
    description: "Personal task lists with due dates and completion status.",
    icon: ListChecks,
    prompt:
      "Build a todo app where users can sign up, log in, and manage their own tasks, each with " +
      "a due date and completion status.",
  },
  {
    id: "healthcare",
    title: "Healthcare Management",
    description: "Doctors manage patients, appointments, and medical records.",
    icon: HeartPulse,
    prompt:
      "Build a healthcare system where doctors can manage patients and schedule appointments. " +
      "Patient medical records must be encrypted and HIPAA compliant.",
  },
  {
    id: "ecommerce",
    title: "E-commerce Platform",
    description: "Customers browse products and check out with Stripe.",
    icon: ShoppingCart,
    prompt:
      "Build an e-commerce store where customers can sign up, browse products, add items to a " +
      "cart, and checkout. Payments are processed through Stripe.",
  },
  {
    id: "school",
    title: "School Management",
    description: "Teachers manage students, courses, and enrollment.",
    icon: GraduationCap,
    prompt:
      "Build a school management system where teachers can manage students, courses, and " +
      "enrollment. Only teachers can edit grades.",
  },
];
