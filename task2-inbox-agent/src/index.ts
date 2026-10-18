import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { apiRouter } from "./api/routes.js";
import { knowledgeClient } from "./client/knowledgeClient.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;

app.use(cors());
app.use(express.json());

app.use("/api/v1", apiRouter);

app.get("/", (req, res) => {
  res.json({
    service: "Task 2: Inbox Agent Microservice (Strict TypeScript)",
    version: "1.0.0",
    docs: "/api/v1/health",
    endpoints: [
      "GET  /api/v1/emails",
      "GET  /api/v1/emails/:id",
      "POST /api/v1/emails/:id/process",
      "POST /api/v1/emails/:id/review",
      "GET  /api/v1/autonomy/status",
      "GET  /api/v1/autonomy/audit",
      "GET  /api/v1/health"
    ]
  });
});

app.listen(PORT, async () => {
  console.log(`[InboxAgent] TypeScript service running on http://127.0.0.1:${PORT}`);
  const kbLive = await knowledgeClient.healthCheck();
  console.log(`[InboxAgent] Task 1 Knowledge Brain connection: ${kbLive ? "ONLINE (Port 8000)" : "OFFLINE / STANDBY"}`);
});

export default app;
