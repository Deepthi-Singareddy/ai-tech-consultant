import { Router, Request, Response } from "express";
import fs from "fs";
import path from "path";
import { CustomerEmail, EmailCategory } from "../types/index.js";
import { emailDrafter } from "../drafter/drafter.js";
import { autonomyGate } from "../autonomy/autonomyGate.js";
import { knowledgeClient } from "../client/knowledgeClient.js";

export const apiRouter = Router();

// Load the 50 customer emails
const emailsFilePath = path.resolve(process.cwd(), "src", "data", "emails.json");
let emailsList: CustomerEmail[] = [];

try {
  emailsList = JSON.parse(fs.readFileSync(emailsFilePath, "utf-8"));
} catch (err) {
  console.error("[InboxRouter] Could not load emails.json:", err);
}

// 1. List all inbound customer emails
apiRouter.get("/emails", (req: Request, res: Response) => {
  const categoryFilter = req.query.category as string;
  if (categoryFilter) {
    return res.json(emailsList.filter((e) => e.expectedCategory === categoryFilter));
  }
  return res.json(emailsList);
});

// 2. Get single email by ID
apiRouter.get("/emails/:id", (req: Request, res: Response) => {
  const email = emailsList.find((e) => e.id === req.params.id);
  if (!email) {
    return res.status(404).json({ error: `Email with ID ${req.params.id} not found` });
  }
  return res.json(email);
});

// 3. Process email (Intent classification + Task 1 KB query + Grounded draft generation)
apiRouter.post("/emails/:id/process", async (req: Request, res: Response) => {
  const email = emailsList.find((e) => e.id === req.params.id);
  if (!email) {
    return res.status(404).json({ error: `Email with ID ${req.params.id} not found` });
  }

  try {
    const draft = await emailDrafter.draftReply(email);
    return res.json({
      email,
      draft
    });
  } catch (err: any) {
    return res.status(500).json({ error: "Failed to generate draft", details: err.message });
  }
});

// 4. Record human review (Approve, Edit, Reject, Escalate)
apiRouter.post("/emails/:id/review", (req: Request, res: Response) => {
  const email = emailsList.find((e) => e.id === req.params.id);
  if (!email) {
    return res.status(404).json({ error: `Email with ID ${req.params.id} not found` });
  }

  const { category, originalDraft, finalSentReply, action, reviewerName, notes } = req.body;

  if (!category || !originalDraft || !finalSentReply || !action) {
    return res.status(400).json({
      error: "Missing required fields: category, originalDraft, finalSentReply, action"
    });
  }

  const record = autonomyGate.recordReview({
    emailId: email.id,
    category: category as EmailCategory,
    originalDraft,
    finalSentReply,
    action,
    reviewerName: reviewerName || "Human Support Lead",
    notes
  });

  return res.json({
    status: "recorded",
    reviewRecord: record,
    updatedCategoryState: autonomyGate.getAllCategoryStates().find((s) => s.category === category)
  });
});

// 5. Autonomy Engine Status across all categories
apiRouter.get("/autonomy/status", (req: Request, res: Response) => {
  return res.json({
    threshold: 20,
    categories: autonomyGate.getAllCategoryStates()
  });
});

// 6. Review Audit Trail
apiRouter.get("/autonomy/audit", (req: Request, res: Response) => {
  return res.json(autonomyGate.getAuditLogs());
});

// 7. Health & Connectivity Check
apiRouter.get("/health", async (req: Request, res: Response) => {
  const kbConnected = await knowledgeClient.healthCheck();
  return res.json({
    status: "healthy",
    service: "Task 2: Inbox Agent (TypeScript)",
    totalEmailsLoaded: emailsList.length,
    knowledgeBrainConnected: kbConnected
  });
});
