import { CustomerEmail, EmailCategory, RiskLevel } from "../types/index.js";

export interface ClassificationResult {
  category: EmailCategory;
  confidence: number;
  riskLevel: RiskLevel;
  urgency: "NORMAL" | "HIGH" | "URGENT";
  reasons: string[];
  policyWarnings: string[];
  extractedKeywords: string[];
}

export class EmailClassifier {
  classify(email: CustomerEmail): ClassificationResult {
    const text = `${email.subject} ${email.body}`.toLowerCase();
    const reasons: string[] = [];
    const policyWarnings: string[] = [];

    // 1. Check High-Risk Policy Triggers First
    const isRefund = /refund|chargeback|money\s*back|cancel\s*(my\s*)?subscription|cancel\s*(my\s*)?account|billing\s*dispute|unauthorized\s*charge/i.test(text);
    const isComplaint = /unacceptable|furious|terrible|broken\s*site|outage|legal\s*action|loss\s*of\s*(revenue|business)|scam|ridiculous|worst/i.test(text);
    const isQuote = /quote|estimate|how\s*much\s*would\s*it\s*cost|pricing\s*for|hourly\s*rate|budget/i.test(text);
    const isProject = /can\s*you\s*build|custom\s*(feature|development|plugin|integration|widget|calculator)|new\s*project|add\s*a\s*new|redesign/i.test(text);
    const isFollowup = /following\s*up|any\s*update|status\s*of|ticket\s*#|checking\s*in\s*on|heard\s*back/i.test(text);
    const isTroubleshooting = /not\s*working|error|failed|fails|issue|problem|bug|stopped\s*working|cannot\s*(login|connect|save)|warning|expired|blocking|not\s*(sending|receiving)|spam|wrong|corrupted/i.test(text);
    const isHowTo = /how\s*do\s*i|how\s*to|where\s*(do|can)\s*i|steps\s*to|is\s*it\s*possible\s*to|guide/i.test(text);

    let category: EmailCategory = "HOW_TO";
    let riskLevel: RiskLevel = "LOW";
    let urgency: "NORMAL" | "HIGH" | "URGENT" = "NORMAL";
    let confidence = 0.88;

    if (isRefund) {
      category = "REFUND_CANCELLATION";
      riskLevel = "HIGH";
      urgency = "HIGH";
      confidence = 0.96;
      reasons.push("Detected financial refund, cancellation, or billing dispute intent.");
      policyWarnings.push("FINANCIAL_RISK: Direct support staff cannot authorize refunds >$100 without manager verification.");
      policyWarnings.push("AUTONOMY_PROHIBITED: Category is permanently restricted from autonomous sending.");
    } else if (isComplaint) {
      category = "COMPLAINT";
      riskLevel = /legal|sue|loss\s*of\s*business/i.test(text) ? "CRITICAL" : "HIGH";
      urgency = "URGENT";
      confidence = 0.94;
      reasons.push("Customer expresses frustration, service outage, or service failure.");
      policyWarnings.push("REPUTATION_RISK: Requires empathetic human review; autonomy strictly blocked.");
    } else if (isQuote) {
      category = "QUOTE_REQUEST";
      riskLevel = "MEDIUM";
      urgency = "NORMAL";
      confidence = 0.92;
      reasons.push("Client is seeking commercial pricing or scoping estimates.");
      policyWarnings.push("COMMERCIAL_RISK: Ensure estimates are labeled as preliminary pending discovery.");
    } else if (isProject) {
      category = "PROJECT_REQUEST";
      riskLevel = "MEDIUM";
      urgency = "NORMAL";
      confidence = 0.90;
      reasons.push("Client proposes new customization or custom development work.");
    } else if (isFollowup) {
      category = "FOLLOW_UP";
      riskLevel = "LOW";
      urgency = /urgent|asap|waiting/i.test(text) ? "HIGH" : "NORMAL";
      confidence = 0.91;
      reasons.push("Follow-up on previously initiated conversation or support ticket.");
    } else if (isTroubleshooting) {
      category = "TROUBLESHOOTING";
      riskLevel = /payment|checkout|stripe/i.test(text) ? "HIGH" : "MEDIUM";
      urgency = "HIGH";
      confidence = 0.93;
      reasons.push("Customer reports technical failure, malfunction, or error behavior.");
    } else {
      category = "HOW_TO";
      riskLevel = "LOW";
      urgency = "NORMAL";
      confidence = isHowTo ? 0.95 : 0.85;
      reasons.push("Standard product usage or configuration inquiry.");
    }

    // Extract core intent keywords
    const extractedKeywords = text
      .replace(/[^\w\s]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length > 4 && !["would", "could", "should", "about", "please", "hello", "thanks"].includes(w))
      .slice(0, 6);

    return {
      category,
      confidence,
      riskLevel,
      urgency,
      reasons,
      policyWarnings,
      extractedKeywords
    };
  }
}

export const emailClassifier = new EmailClassifier();
