import fs from "fs";
import path from "path";
import { EmailCategory, ReviewRecord, AutonomyGateCategoryState } from "../types/index.js";

export class AutonomyGate {
  private stateFilePath: string;
  private auditLogPath: string;
  private states: Map<EmailCategory, AutonomyGateCategoryState>;

  // Categories permanently barred from autonomy due to financial, legal, or reputation blast radius
  private readonly SAFETY_BLACKLIST: Set<EmailCategory> = new Set([
    "REFUND_CANCELLATION",
    "COMPLAINT"
  ]);

  private readonly AUTONOMY_THRESHOLD = 20;
  private readonly UNEDITED_DIFF_TOLERANCE = 0.05; // 5% max deviation to qualify as "unedited"

  constructor(dataDir = path.resolve(process.cwd(), "data")) {
    fs.mkdirSync(dataDir, { recursive: true });
    this.stateFilePath = path.join(dataDir, "autonomy_state.json");
    this.auditLogPath = path.join(dataDir, "review_audit.json");
    this.states = new Map();
    this.initializeState();
  }

  private initializeState() {
    const allCategories: EmailCategory[] = [
      "HOW_TO",
      "TROUBLESHOOTING",
      "PROJECT_REQUEST",
      "REFUND_CANCELLATION",
      "COMPLAINT",
      "QUOTE_REQUEST",
      "FOLLOW_UP"
    ];

    if (fs.existsSync(this.stateFilePath)) {
      try {
        const raw = JSON.parse(fs.readFileSync(this.stateFilePath, "utf-8"));
        for (const item of raw) {
          this.states.set(item.category, item);
        }
      } catch (err) {
        console.warn("[AutonomyGate] Could not load state file. Initializing defaults.");
      }
    }

    for (const cat of allCategories) {
      if (!this.states.has(cat)) {
        this.states.set(cat, {
          category: cat,
          consecutiveUneditedApprovals: 0,
          isAutonomousActive: false,
          isSafetyBlacklisted: this.SAFETY_BLACKLIST.has(cat),
          totalApproved: 0,
          totalEdited: 0,
          totalRejected: 0
        });
      }
    }
    this.saveState();
  }

  private saveState() {
    try {
      const arr = Array.from(this.states.values());
      fs.writeFileSync(this.stateFilePath, JSON.stringify(arr, null, 2), "utf-8");
    } catch (err) {
      console.error("[AutonomyGate] Failed to persist autonomy state:", err);
    }
  }

  /**
   * Levenshtein Distance implementation for string diff calculation
   */
  calculateEditDistance(s1: string, s2: string): number {
    const m = s1.length;
    const n = s2.length;
    if (m === 0) return n;
    if (n === 0) return m;

    const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        const cost = s1[i - 1] === s2[j - 1] ? 0 : 1;
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1,      // deletion
          dp[i][j - 1] + 1,      // insertion
          dp[i - 1][j - 1] + cost // substitution
        );
      }
    }

    return dp[m][n];
  }

  calculateEditDistanceRatio(originalDraft: string, finalSent: string): number {
    const maxLen = Math.max(originalDraft.length, finalSent.length);
    if (maxLen === 0) return 0.0;
    const dist = this.calculateEditDistance(originalDraft.trim(), finalSent.trim());
    return Math.min(1.0, Math.round((dist / maxLen) * 1000) / 1000);
  }

  /**
   * Records human review action, updates consecutive counts, and enforces autonomy gates
   */
  recordReview(record: Omit<ReviewRecord, "id" | "reviewTimestamp" | "editDistanceRatio">): ReviewRecord {
    const diffRatio = this.calculateEditDistanceRatio(record.originalDraft, record.finalSentReply);
    const fullRecord: ReviewRecord = {
      ...record,
      id: `REV-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      editDistanceRatio: diffRatio,
      reviewTimestamp: new Date().toISOString()
    };

    const state = this.states.get(record.category)!;

    if (record.action === "REJECT" || record.action === "ESCALATE") {
      state.totalRejected++;
      state.consecutiveUneditedApprovals = 0;
      state.isAutonomousActive = false;
      state.lastResetReason = `Manual ${record.action}: ${record.notes || "Draft rejected"}`;
      state.lastResetAt = fullRecord.reviewTimestamp;
    } else if (record.action === "EDIT" || diffRatio >= this.UNEDITED_DIFF_TOLERANCE) {
      state.totalEdited++;
      state.consecutiveUneditedApprovals = 0;
      state.isAutonomousActive = false;
      state.lastResetReason = `Human modified draft (${(diffRatio * 100).toFixed(1)}% edit distance)`;
      state.lastResetAt = fullRecord.reviewTimestamp;
    } else if (record.action === "APPROVE" && diffRatio < this.UNEDITED_DIFF_TOLERANCE) {
      state.totalApproved++;
      state.consecutiveUneditedApprovals++;

      // Check if threshold reached and not blacklisted
      if (
        state.consecutiveUneditedApprovals >= this.AUTONOMY_THRESHOLD &&
        !state.isSafetyBlacklisted
      ) {
        state.isAutonomousActive = true;
      }
    }

    this.saveState();
    this.appendAuditLog(fullRecord);

    return fullRecord;
  }

  private appendAuditLog(record: ReviewRecord) {
    try {
      let logs: ReviewRecord[] = [];
      if (fs.existsSync(this.auditLogPath)) {
        logs = JSON.parse(fs.readFileSync(this.auditLogPath, "utf-8"));
      }
      logs.unshift(record);
      fs.writeFileSync(this.auditLogPath, JSON.stringify(logs.slice(0, 500), null, 2), "utf-8");
    } catch (err) {
      console.error("[AutonomyGate] Failed to append review audit log:", err);
    }
  }

  isAutonomousAllowed(category: EmailCategory): boolean {
    const state = this.states.get(category);
    if (!state) return false;
    if (state.isSafetyBlacklisted) return false;
    return state.isAutonomousActive && state.consecutiveUneditedApprovals >= this.AUTONOMY_THRESHOLD;
  }

  getAllCategoryStates(): AutonomyGateCategoryState[] {
    return Array.from(this.states.values());
  }

  getAuditLogs(): ReviewRecord[] {
    if (fs.existsSync(this.auditLogPath)) {
      try {
        return JSON.parse(fs.readFileSync(this.auditLogPath, "utf-8"));
      } catch {
        return [];
      }
    }
    return [];
  }
}

export const autonomyGate = new AutonomyGate();
