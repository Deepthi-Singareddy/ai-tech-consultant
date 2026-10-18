import assert from "node:assert";
import { emailClassifier } from "../src/classifier/classifier.js";
import { autonomyGate } from "../src/autonomy/autonomyGate.js";
import { emailDrafter } from "../src/drafter/drafter.js";
import { CustomerEmail } from "../src/types/index.js";

async function runInboxUnitTests() {
  console.log("==================================================");
  console.log("RUNNING TASK 2 INBOX AGENT UNIT TESTS (TYPESCRIPT)");
  console.log("==================================================");

  // Test 1: Classification - Refund & Cancellation High Risk
  const refundEmail: CustomerEmail = {
    id: "TEST-01",
    sender: "client@example.com",
    senderName: "Bob",
    subject: "Please cancel my subscription and refund my card",
    body: "I was billed $250 without authorization. Please cancel and refund immediately.",
    receivedAt: new Date().toISOString()
  };
  const refundClass = emailClassifier.classify(refundEmail);
  assert.strictEqual(refundClass.category, "REFUND_CANCELLATION");
  assert.strictEqual(refundClass.riskLevel, "HIGH");
  assert.ok(refundClass.policyWarnings.some((w) => w.includes("FINANCIAL_RISK")));
  console.log("✔ Test 1: Refund classification & high-risk policy trigger passed.");

  // Test 2: Classification - Complaint Critical Risk
  const complaintEmail: CustomerEmail = {
    id: "TEST-02",
    sender: "angry@example.com",
    senderName: "Alice",
    subject: "UNACCEPTABLE: Major server outage broke our site during press launch",
    body: "Our website was offline for 3 hours. We lost thousands in revenue and our legal team is reviewing this.",
    receivedAt: new Date().toISOString()
  };
  const complaintClass = emailClassifier.classify(complaintEmail);
  assert.strictEqual(complaintClass.category, "COMPLAINT");
  assert.strictEqual(complaintClass.riskLevel, "CRITICAL");
  console.log("✔ Test 2: Complaint classification & critical risk detection passed.");

  // Test 3: Classification - How-To Low Risk
  const howToEmail: CustomerEmail = {
    id: "TEST-03",
    sender: "user@example.com",
    senderName: "Charlie",
    subject: "How do I connect Stripe payment gateway in admin?",
    body: "Can you send the guide for setting up Stripe API keys in Finance settings?",
    receivedAt: new Date().toISOString()
  };
  const howToClass = emailClassifier.classify(howToEmail);
  assert.strictEqual(howToClass.category, "HOW_TO");
  assert.strictEqual(howToClass.riskLevel, "LOW");
  console.log("✔ Test 3: How-To classification & low-risk detection passed.");

  // Test 4: Edit Distance Calculation
  const originalDraft = "Hi Sarah, you can connect Stripe under Finance > Payment Gateways. Best regards, Support Team.";
  const minorEdit = "Hi Sarah, you can connect Stripe under Finance > Payment Gateways. Best regards, AI Support Team.";
  const majorEdit = "Hello Sarah, please ignore that. We need to manually schedule a zoom call to fix your database.";

  const minorDiff = autonomyGate.calculateEditDistanceRatio(originalDraft, minorEdit);
  const majorDiff = autonomyGate.calculateEditDistanceRatio(originalDraft, majorEdit);

  assert.ok(minorDiff < 0.05, `Minor diff should be < 0.05, was ${minorDiff}`);
  assert.ok(majorDiff > 0.30, `Major diff should be > 0.30, was ${majorDiff}`);
  console.log(`✔ Test 4: Levenshtein diff metrics passed (Minor: ${(minorDiff * 100).toFixed(1)}%, Major: ${(majorDiff * 100).toFixed(1)}%).`);

  // Test 5: 20-Consecutive Autonomy Gate Threshold & Safety Blacklist
  const catState = autonomyGate.getAllCategoryStates().find((s) => s.category === "HOW_TO")!;
  const initialStreak = catState.consecutiveUneditedApprovals;

  // Record approvals up to 20
  for (let i = 1; i <= 20; i++) {
    autonomyGate.recordReview({
      emailId: `STREAK-${i}`,
      category: "HOW_TO",
      originalDraft: originalDraft,
      finalSentReply: originalDraft, // 0 diff
      action: "APPROVE",
      reviewerName: "QA Engineer"
    });
  }

  assert.strictEqual(autonomyGate.isAutonomousAllowed("HOW_TO"), true, "HOW_TO should be autonomous after 20 unedited approvals");
  console.log("✔ Test 5a: 20-consecutive approvals successfully granted autonomous status to HOW_TO.");

  // Test 5b: Demotion on human edit
  autonomyGate.recordReview({
    emailId: "STREAK-RESET",
    category: "HOW_TO",
    originalDraft: originalDraft,
    finalSentReply: majorEdit, // Significant human modification
    action: "EDIT",
    reviewerName: "QA Engineer"
  });

  assert.strictEqual(autonomyGate.isAutonomousAllowed("HOW_TO"), false, "HOW_TO autonomy must be immediately revoked after human edit");
  console.log("✔ Test 5b: Autonomous status successfully revoked upon human modification.");

  // Test 5c: Permanent Safety Blacklist for Refund/Cancellation
  for (let i = 1; i <= 25; i++) {
    autonomyGate.recordReview({
      emailId: `REFUND-STREAK-${i}`,
      category: "REFUND_CANCELLATION",
      originalDraft: "Refund draft",
      finalSentReply: "Refund draft",
      action: "APPROVE",
      reviewerName: "QA Engineer"
    });
  }
  assert.strictEqual(autonomyGate.isAutonomousAllowed("REFUND_CANCELLATION"), false, "REFUND_CANCELLATION must NEVER be autonomous due to safety blacklist");
  console.log("✔ Test 5c: Permanent safety blacklist enforced (REFUND_CANCELLATION blocked from autonomy).");

  // Test 6: Draft Generation Pipeline
  const draft = await emailDrafter.draftReply(howToEmail);
  assert.strictEqual(draft.category, "HOW_TO");
  assert.ok(draft.draftReply.includes("Stripe") || draft.draftReply.includes("Finance") || draft.draftReply.includes("Dashboard"));
  console.log("✔ Test 6: Grounded email draft generated successfully.");

  console.log("==================================================");
  console.log("ALL TASK 2 INBOX AGENT UNIT TESTS PASSED (6/6)");
  console.log("==================================================");
}

runInboxUnitTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
