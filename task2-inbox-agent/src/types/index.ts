import { z } from "zod";

export const EmailCategoryEnum = z.enum([
  "HOW_TO",
  "TROUBLESHOOTING",
  "PROJECT_REQUEST",
  "REFUND_CANCELLATION",
  "COMPLAINT",
  "QUOTE_REQUEST",
  "FOLLOW_UP"
]);
export type EmailCategory = z.infer<typeof EmailCategoryEnum>;

export const RiskLevelEnum = z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
export type RiskLevel = z.infer<typeof RiskLevelEnum>;

export interface CustomerEmail {
  id: string;
  sender: string;
  senderName: string;
  subject: string;
  body: string;
  receivedAt: string;
  expectedCategory?: EmailCategory;
  expectedRisk?: RiskLevel;
}

export interface KnowledgeCitation {
  article_id: string;
  title: string;
  url: string;
  category: string;
  section_heading?: string;
  snippet: string;
  relevance: number;
}

export interface Task1QueryResponse {
  query: string;
  answer: string;
  status: "answered" | "insufficient_evidence" | "escalated";
  confidence: number;
  sources: KnowledgeCitation[];
  images: Array<{
    url: string;
    caption: string;
    visual_description: string;
  }>;
  needs_escalation: boolean;
  escalation_id?: string;
}

export interface EmailDraft {
  emailId: string;
  category: EmailCategory;
  riskLevel: RiskLevel;
  urgency: "NORMAL" | "HIGH" | "URGENT";
  summary: string;
  draftReply: string;
  sourcesUsed: KnowledgeCitation[];
  requiresHumanApproval: boolean;
  policyWarnings: string[];
  suggestedAction: string;
  generatedAt: string;
  latencyMs: number;
  modelUsed: string;
}

export interface ReviewRecord {
  id: string;
  emailId: string;
  category: EmailCategory;
  originalDraft: string;
  finalSentReply: string;
  action: "APPROVE" | "EDIT" | "REJECT" | "ESCALATE";
  editDistanceRatio: number; // 0.0 to 1.0 (Levenshtein / length)
  reviewerName: string;
  reviewTimestamp: string;
  notes?: string;
}

export interface AutonomyGateCategoryState {
  category: EmailCategory;
  consecutiveUneditedApprovals: number;
  isAutonomousActive: boolean;
  isSafetyBlacklisted: boolean;
  totalApproved: number;
  totalEdited: number;
  totalRejected: number;
  lastResetReason?: string;
  lastResetAt?: string;
}
