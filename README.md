# AI Tech Consultant

The **AI Tech Consultant** is a production-grade multi-agent microservice suite designed to solve the economic bottleneck created by AI-accelerated code generation. By automating product knowledge discovery, customer inbox triage, and meeting-to-scope engineering, it enables software agencies and SaaS providers to increase operational delivery throughput by **10x to 20x**.

---

## Architecture at a Glance

The system is composed of three connected tasks communicating exclusively over REST APIs:

1. **Task 1 — The Knowledge Brain (`task1-knowledge-brain`) [Python/FastAPI :8000]:**
   Single Source of Truth (SSOT). Polite, resumable sitemap crawler for the Brilliant Directories Solution Center. Extracts HTML articles and multimodal screenshot context into a hybrid dense vector + BM25 keyword store. Enforces strict URL citations, confidence thresholding, and a human expert escalation queue (`/escalations`).
2. **Task 2 — The Inbox Agent (`task2-inbox-agent`) [Strict TypeScript/Node :3000]:**
   Autonomous triage and drafting service calling Task 1's API. Categorizes emails across 7 intents with risk scoring (1–5). Features a **20-consecutive unedited approval autonomy gate** with instant reset on human edits ($>0.05$) and permanent safety blacklists for refund disputes and complaints. Evaluated on **50 realistic customer emails**.
3. **Task 3 — Meeting to Scope of Work (`task3-meeting-to-scope`) [Python/FastAPI :8001]:**
   Multi-agent pipeline (Analyst $\to$ Feasibility $\to$ WBS Estimator $\to$ Scope Architect $\to$ Proposal Executive). Checks Task 1 API to resolve requirements using native settings ($0 dev cost) vs. custom development. Features a **Scope Diff Engine** that compares follow-up meetings against the approved baseline to prevent scope creep.
4. **Unified Command Cockpit (`web-studio`) [Vanilla CSS/JS/HTML :5000]:**
   Single-pane-of-glass executive dashboard connecting all microservices for non-technical stakeholders.

---

## Quick Start (One Command)

### Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **Node.js 18+** (tested on Node.js 24)
- Modern web browser (Chrome, Edge, Firefox)

### Launch Entire Suite

#### Windows
Double-click or run from terminal:
```bat
run_all.bat
```

#### Unix / macOS
```bash
chmod +x run_all.sh
./run_all.sh
```

The script starts all 4 services and automatically opens the **Unified Command Cockpit** at:  
👉 **`http://127.0.0.1:5000`**

---

## Service Endpoints & API Documentation

| Service | Port | Description | Interactive API Docs |
| :--- | :--- | :--- | :--- |
| **Unified Command Cockpit** | `5000` | Executive Web Dashboard | `http://127.0.0.1:5000` |
| **Task 1: Knowledge Brain** | `8000` | Python FastAPI Knowledge Microservice | `http://127.0.0.1:8000/docs` |
| **Task 2: Inbox Agent** | `3000` | TypeScript Customer Email Agent | `http://127.0.0.1:3000/api/v1/health` |
| **Task 3: Meeting to Scope** | `8001` | Python Multi-Agent Scope & WBS Studio | `http://127.0.0.1:8001/docs` |

---

## Running Automated Tests & Evals

### Run All Unit Tests (16/16 Passed)
```bat
test_all.bat
```
*(Runs pytest for Tasks 1 & 3, and TypeScript test runner for Task 2).*

### Run All Evaluations (70/70 Cases Across 3 Tasks)
```bat
eval_all.bat
```
*(Benchmarks Claude 3.5 Sonnet vs. Haiku across all 70 test cases, tracking precision, latency, and cost in USD and INR).*

---

## Zero-Friction Offline Readiness
The project works completely **out-of-the-box** with zero initial configuration. It includes pre-packaged seed knowledge fixtures and deterministic grounded fallbacks. To connect live Anthropic Claude models, simply set your key in `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```
