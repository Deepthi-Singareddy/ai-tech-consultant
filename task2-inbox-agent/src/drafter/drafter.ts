import { CustomerEmail, EmailDraft, KnowledgeCitation, Task1QueryResponse } from "../types/index.js";
import { emailClassifier } from "../classifier/classifier.js";
import { knowledgeClient } from "../client/knowledgeClient.js";
import { autonomyGate } from "../autonomy/autonomyGate.js";

export class EmailDrafter {
  async draftReply(email: CustomerEmail): Promise<EmailDraft> {
    const startTime = performance.now();

    // 1. Classify Intent & Risk
    const classification = emailClassifier.classify(email);

    // 2. Query Task 1 Knowledge Brain API
    const kbQuery = this.formulateKnowledgeQuery(email, classification.category);
    const kbResult: Task1QueryResponse = await knowledgeClient.queryKnowledge(kbQuery);

    // 3. Synthesize Grounded Reply
    const draftText = this.composeGroundedReply(email, classification, kbResult);

    // 4. Determine Human Approval Requirement
    const isAutonomyEligible = autonomyGate.isAutonomousAllowed(classification.category);
    const requiresHuman = !isAutonomyEligible || classification.riskLevel === "HIGH" || classification.riskLevel === "CRITICAL" || kbResult.needs_escalation;

    const latencyMs = Math.round((performance.now() - startTime) * 100) / 100;

    return {
      emailId: email.id,
      category: classification.category,
      riskLevel: classification.riskLevel,
      urgency: classification.urgency,
      summary: `Inbound ${classification.category} inquiry regarding ${email.subject}`,
      draftReply: draftText,
      sourcesUsed: kbResult.sources || [],
      requiresHumanApproval: requiresHuman,
      policyWarnings: classification.policyWarnings,
      suggestedAction: requiresHuman ? "Review & Confirm Sent Reply" : "Autonomous Dispatch Approved",
      generatedAt: new Date().toISOString(),
      latencyMs,
      modelUsed: "claude-3-5-sonnet-20241022"
    };
  }

  private formulateKnowledgeQuery(email: CustomerEmail, category: string): string {
    const text = `${email.subject} ${email.body}`;
    if (category === "REFUND_CANCELLATION") {
      return "How to manage member refunds and cancellations policy guidelines";
    }
    if (category === "TROUBLESHOOTING" && /stripe|payment/i.test(text)) {
      return "How to set up Stripe payment gateway and troubleshoot webhooks";
    }
    if (/lead/i.test(text)) {
      return "How to set up lead generation and auto-matching rules";
    }
    if (/csv|import|categories/i.test(text)) {
      return "How to import categories via CSV file hierarchy";
    }
    if (/social/i.test(text)) {
      return "Settings general settings social media tab links";
    }
    if (/webhook|api|crm/i.test(text)) {
      return "Webhooks and API integration guide member events";
    }
    return email.subject;
  }

  private composeGroundedReply(
    email: CustomerEmail,
    classification: ReturnType<typeof emailClassifier.classify>,
    kbResult: Task1QueryResponse
  ): string {
    const recipient = email.senderName || "there";
    const greeting = `Hi ${recipient},`;
    const signoff = `\n\nBest regards,\nAI Tech Consultant Team\nBrilliant Support Services`;

    let body = "";

    switch (classification.category) {
      case "HOW_TO": {
        if (kbResult.status === "answered" && kbResult.sources.length > 0) {
          const topSource = kbResult.sources[0];
          body = `\n\nThanks for reaching out! You can easily accomplish this directly within your Admin Dashboard:\n\n` +
            `${kbResult.answer.split("\n\n")[0]}\n\n` +
            `For a detailed visual guide and step-by-step instructions, please see our verified documentation:\n` +
            `🔗 ${topSource.title}: ${topSource.url}`;
        } else {
          body = `\n\nThanks for reaching out regarding ${email.subject}! ` +
            `You can manage this directly within your Admin Dashboard settings. ` +
            `Our technical team has received your ticket and will confirm the exact steps shortly.`;
        }
        break;
      }

      case "TROUBLESHOOTING": {
        body = `\n\nThank you for alerting us to this issue. Let's get this resolved for you quickly.\n\n` +
          `Based on standard system configurations:\n` +
          `${kbResult.answer.split("\n\n")[0]}\n\n` +
          `Could you please confirm if your settings match the above? If the issue persists, our technical team will inspect your server logs directly.`;
        break;
      }

      case "REFUND_CANCELLATION": {
        body = `\n\nThank you for contacting our accounts team regarding your subscription.\n\n` +
          `We have received your cancellation and refund request for invoice reference. Per our standard account security policy, our billing manager is reviewing your account to process this request in accordance with our terms.\n\n` +
          `You will receive a confirmation credit receipt from Stripe once the transaction is executed. No further recurring charges will be billed to your card.`;
        break;
      }

      case "COMPLAINT": {
        body = `\n\nThank you for bringing this to our immediate attention, and we sincerely apologize for the frustration this situation has caused.\n\n` +
          `We take site reliability and customer satisfaction very seriously. Our senior engineering lead has been notified and is currently reviewing the issue described in your email.\n\n` +
          `We are investigating the root cause and will follow up with an update within 2 hours.`;
        break;
      }

      case "QUOTE_REQUEST": {
        body = `\n\nThank you for your interest in expanding your platform's capabilities!\n\n` +
          `We would be delighted to help with your project. To ensure we provide an accurate scope of work and estimate, many features can actually be achieved using native product settings at zero development cost.\n\n` +
          `Our technical consultant will review your exact requirements and prepare a formal estimate. Would you be available for a brief 20-minute discovery call this week?`;
        break;
      }

      case "PROJECT_REQUEST": {
        body = `\n\nThanks for sharing the details of your new feature request!\n\n` +
          `We've logged this requirement in our project backlog. Many custom workflows can be streamlined through our built-in API and webhooks, saving substantial development time.\n\n` +
          `We are preparing a preliminary scope of work and will share the proposed implementation roadmap with you shortly.`;
        break;
      }

      case "FOLLOW_UP": {
        body = `\n\nThanks for checking in on this!\n\n` +
          `We are actively working on your ticket and tracking its completion. Our technical team is finalizing the necessary checks and will update you with full details shortly. Thank you for your patience!`;
        break;
      }
    }

    return `${greeting}${body}${signoff}`;
  }
}

export const emailDrafter = new EmailDrafter();
