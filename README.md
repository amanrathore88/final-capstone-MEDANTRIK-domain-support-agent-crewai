# MEDANTRIK ASSIST — Intelligent Device Support OS

> **Official Capstone Submission Domain:** `Chat Support System`  
> **Benchmark Technical Specification:** 16-Task Architecture (adapted from the reference technical rubric to Medantrik Medtech)  
> **Target Enterprise:** Medantrik Medtech Pvt. Ltd. ([https://medantrik.com/](https://medantrik.com/))  
> **GitHub Repository:** [https://github.com/amanrathore88/final-capstone-MEDANTRIK-domain-support-agent-crewai](https://github.com/amanrathore88/final-capstone-MEDANTRIK-domain-support-agent-crewai)  
> **Project Mode:** Local-First, Zero-Paid-Dependency, Fully Deterministic AI Multi-Agent Prototype  
> **Student Author Disclaimer:** This capstone is an independent student academic demonstration for respiratory medtech device support. It is not an official product of Medantrik Medtech Pvt. Ltd. All ticket records, customer identities, SLAs, and refund terms are strictly synthetic. Device product descriptions are sourced from Medantrik's public portal.

---

## 1. Executive Summary & Architecture

**MEDANTRIK ASSIST** is a multi-agent AI operating system engineered for customer, clinical, and technical device support across Medantrik's respiratory device portfolio (**OxySense**, **NODex**, and **Iron Lung**). 

The system implements evidence-grounded answers via dual-strategy ChromaDB retrieval, deterministic keyless **CrewAI** 3-agent orchestration (`Retrieval Agent`, `Ticket Lookup Agent`, `Response Composer`), multi-turn **LangChain** conversation memory, dual-agent **AutoGen** structured compliance review (`Policy Compliance Reviewer` and `Final Editor`), strict PII sanitization (Indian phone number masking), clinical safety triage, prompt-injection defense, response-level governance, semantic policy caching, and a responsive **React 18 + TypeScript** desktop/mobile interface.

### Zero-Key Offline Execution & Telemetry Guarantee
As mandated by the technical rubric:
- **`MOCK_LLM=true`**: All agents (CrewAI, AutoGen, LLM-as-judge) execute under deterministic, keyless mock adapters with zero paid API keys required.
- **Telemetry Disabled**: CrewAI and OpenTelemetry outbound network pings are strictly disabled prior to framework import via:
  ```python
  os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
  os.environ["OTEL_SDK_DISABLED"] = "true"
  os.environ["CREWAI_TRACING_ENABLED"] = "false"
  os.environ["ANONYMIZED_TELEMETRY"] = "false"
  ```
- **Local Vectors**: Embeddings (`all-MiniLM-L6-v2`) and vector storage (`ChromaDB`) run 100% locally.

```
                      +-------------------------------------------------------------+
                      |         MEDANTRIK ASSIST — USER INTERFACES                  |
                      |  * Responsive React 18 / TypeScript Single-Page Application |
                      |  * WebSocket Streaming + REST Fallback (:8000)              |
                      +------------------------------+------------------------------+
                                                     |
                                                     v
                      +-------------------------------------------------------------+
                      |              INPUT GUARDRAILS & ROUTING                     |
                      |  * Indian Mobile Phone Masking ([PHONE_MASKED])             |
                      |  * Regex & Heuristic Prompt Injection Neutralization         |
                      |  * Medical Safety & Clinical Emergency Triage                |
                      |  * Governance Budget Filter (50k tokens / $0.10 max)        |
                      +------------------------------+------------------------------+
                                                     |
                                                     v
                                      +--------------+--------------+
                                      | Normalized Cache Hit Check  |
                                      +--------------+--------------+
                                                     |
                        [Cache Miss]                 |               [Cache Hit]
                             +-----------------------+-----------------------+
                             |                                               |
                             v                                               v
+-----------------------------------------------------------+     +--------------------+
|               CrewAI 3-AGENT ORCHESTRATION                |     | Immediate Zero-Cost|
|  * BaseLLM Mock Adapter (Deterministic, Offline)          |     | Cached Policy Term |
|                                                           |     +--------------------+
|  1. Retrieval Agent   --> ChromaDB Vector RAG (Dual-index)|
|  2. Lookup Agent      --> SQLite Synthetic Ticket Engine  |
|  3. Composer Agent    --> Evidence Synthesis & Grounding  |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|          AutoGen DUAL-AGENT STRUCTURED REVIEW             |
|  * Policy Compliance Reviewer checks Grounding & Tone     |
|  * Final Editor emits Pydantic Structured Verdict         |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|               PERSISTENCE & AUDIT TRAILS                  |
|  * LangChain Session Context Memory                       |
|  * Normalized Policy Semantic Cache (Private Excluded)     |
|  * SQLite Synthetic Tickets, Messages, & Audit Trails     |
|  * Masked JSONL Structured Observability Logs             |
+-----------------------------------------------------------+
```

---

## 2. Verified Public Facts vs. Synthetic Demonstration Data

To guarantee integrity and safety, the platform maintains strict segregation between publicly verified company facts and synthetic student demonstration entities:

| Data Class | Data Elements | Source / Provenance | Safe Handling Policy |
|---|---|---|---|
| **Verified Public Facts** | Medantrik company profile, IIT Kanpur incubation, official portal (`https://medantrik.com/`), and product overviews for **OxySense** (inline oxygen analyzer), **NODex** (smart respiratory device), and **Iron Lung** (smart respiration system). | Sourced directly from public web pages (`https://medantrik.com/?p=1930`). Stored in `data/product_catalog.json`. | Tagged with `source_type: "PUBLIC_VERIFIED_FACT"`. Rendered with distinctive cyan badge in evidence drawers. |
| **Synthetic Demo Policies** | 12 policy documents covering ticket priorities, SLAs, escalation matrix, refunds, channels, hours, repeat complaints, service credits, feedback, VIP handling, outage broadcasts, and data retention. | Original student synthetic policies authored for this capstone in `knowledge_base/*.md`. | Tagged with `source_type: "SYNTHETIC_DEMO_POLICY"`. Explicitly warns user of fictional simulation. |
| **Synthetic Ticket Records** | 80 seeded customer tickets with categories, statuses, products, resolution hours, and escalation flags. | Deterministically generated via `dataset.py` with fixed seed `20261107`. | Zero real patient or customer data. PII numbers masked automatically. |

### Dataset Design Choices & Mathematical Parameters (Task 1 & Task 6)

To enable deterministic grading and reproducibility:
- **RNG Seed:** `20261107`
- **Total Records:** `80` synthetic support tickets.
- **Category Weights:** `(14, 34, 12, 22, 18)` corresponding to:
  - `Billing`: 10 tickets (12.5%)
  - `Technical Issue`: 33 tickets (41.25%)
  - `Account Access`: 6 tickets (7.5%)
  - `Product Defect`: 16 tickets (20.0%)
  - `General Inquiry`: 15 tickets (18.75%)
  *(Every category has $\ge 3$ records)*
- **Status Weights:** `(22, 26, 12, 22, 18)` corresponding to:
  - `Open`: 17 tickets (21.25%)
  - `In Progress`: 14 tickets (17.5%)
  - `Escalated`: 12 tickets (15.0%)
  - `Resolved`: 16 tickets (20.0%)
  - `Closed`: 21 tickets (26.25%)
  *(Every status has $\ge 1$ record)*
- **Escalated Rate:** **17.5%** of all tickets have `escalated=True` (strictly inside the required 10%–30% target band).
- **Resolution Time Hours Bounds & Reasoning:**
  - `Billing`: 2–72 hours
  - `Technical Issue`: 2–144 hours
  - `Account Access`: 1–48 hours
  - `Product Defect`: 8–168 hours
  - `General Inquiry`: 1–24 hours
  *Reasoning:* Respiratory medical device support ranges from quick informational or account inquiries (1–24 hours) to complex hardware diagnostic and safety inspections (up to 168 hours / 7 days) requiring biomedical engineering coordination.
- **Escalation Score Formula & Justification:**
  $$\text{escalation\_score} = 0.50 \times \text{escalated} + 0.30 \times \left(\frac{\min(\text{days\_since\_created}, 30)}{30}\right) + 0.20 \times \left(\frac{\min(\text{reopen\_count}, 3)}{3}\right)$$
  - Recommended escalation threshold: **`0.3667`**
  - *Justification:* Corresponds to the empirical 80th percentile of the synthetic distribution, identifying tickets that combine critical escalation flags with aging unresolved durations or repeat reopens.

---

## 3. Requirements Traceability Matrix (All 16 Acceptance Tasks)

Every task from `docs/ACCEPTANCE_MATRIX.md` has been verified with tests and logged evidence:

| Task # | Technical Requirement | Implementation Module | Acceptance Evidence File | Measured Empirical Metric / Outcome |
|---|---|---|---|---|
| **Task 1** | Synthetic Ticket Dataset | `dataset.py`, `database/db.py` | `evidence/dataset_report.json` | **80 seeded tickets**, Seed `20261107`, 5 categories (each ≥3), 5 statuses, **17.5% escalation rate** (in target 10–30% band). |
| **Task 2** | Knowledge Base & Catalog | `knowledge_base/*.md`, `data/product_catalog.json` | `knowledge_base/` | **12 original 2–5 sentence policy docs** + verified public catalog for OxySense, NODex, and Iron Lung. |
| **Task 3** | Dual Chroma Chunking | `rag/chunking.py`, `rag/core.py` | `evidence/index_stats.json` | **33 fixed-overlap chunks** (240 char / 50 overlap) & **60 sentence chunks** indexed into Chroma collections. |
| **Task 4** | Empirical Threshold Calibration | `rag/calibration.py` | `evidence/calibration.json` | Derived threshold **`0.3221`** with **`0.3186`** separation margin between in-scope (min 0.4814) and out-of-scope (max 0.1628). |
| **Task 5** | Retrieval Precision & Recall Eval | `rag/evaluation.py` | `evidence/retrieval_comparison.md`, `evidence/retrieval_eval.json` | Fixed-overlap: **Recall 1.000**, Precision 0.467, **F1 0.6364** vs Sentence: Recall 0.800, F1 0.5895. **Recommended: fixed_overlap**. |
| **Task 6** | Synthetic Ticket Lookup Tool | `support/tickets.py` | `tests/test_ticket_tool.py` | `check_support_ticket_status` returns deterministic fixture, status, hours, and escalation score in `[0.0, 1.0]`. |
| **Task 7** | CrewAI 3-Agent Kickoff | `support/crew.py` | `evidence/crew_calls.json` | 3 native CrewAI agents orchestrated via `crew.kickoff()`; tool invocations recorded in `evidence/crew_calls.json`. |
| **Task 8** | Multi-Turn Session Memory | `support/session.py` | `evidence/memory_transcripts.json` | LangChain session context carried across follow-up queries; fresh sessions isolated. |
| **Task 9** | Pydantic Structured Responses | `support/models.py` | `tests/test_crew.py`, `tests/test_api.py` | Validated `SupportResponse` Pydantic contracts for 100% of pipeline and API outputs. |
| **Task 10** | Guardrails & Medical Safety | `support/guardrails.py` | `tests/test_guardrails.py` | Indian phone masking (`[PHONE_MASKED]`), prompt injection rejection, grounding check, emergency clinical triage. |
| **Task 11** | FastAPI REST & WebSockets | `api/app.py` | `tests/test_api.py`, `tests/test_websocket.py` | 7 HTTP routes (`/health`, `/ask`, `/tickets`, `/reset-session`, etc.) + live WebSocket `/ws/chat` with graceful disconnect. |
| **Task 12** | Structured JSONL Masked Logs | `api/logging.py` | `evidence/masked_logs.jsonl` | Exactly one JSONL entry per request with `trace_id`, latency, session, tokens, and masked query. Zero raw phone numbers. |
| **Task 13** | 15-Case LLM-Judge Evaluation | `evaluation/judge.py`, `evaluation/run_eval.py` | `evidence/evaluation_results.json` | Evaluated 15 policy & negative scenarios: **Accuracy 4.20**, **Grounding 4.20**, **Completeness 5.00**, **Safety 5.00**, **Overall 4.60**. |
| **Task 14** | AutoGen 2-Agent Structured Review | `support/review.py` | `evidence/review_cases.json` | `Policy_Compliance_Reviewer` + `Final_Editor` in `RoundRobinGroupChat`; proven approval & revision test cases. |
| **Task 15** | Least Autonomy & High-Risk Governance | `support/governance.py` | `tests/test_crew.py`, `tests/test_session_and_cache.py` | Only Lookup Agent authorized for ticket data; justified **HIGH** medical device risk tier; 50k token cap enforced. |
| **Task 16** | Semantic Policy Response Cache | `support/cache.py` | `evidence/cache_hit.json` | 1st call miss (1 tool call), 2nd call hit (0 tool calls); ticket-specific and clinical queries barred from caching. |

---

## 4. Medical Safety & Clinical Boundaries

In compliance with medical software safety practices:

1. **No Clinical Interpretations:** The assistant will **never** diagnose respiratory conditions, interpret spirometry parameters, evaluate blood oxygen saturation levels, or calculate medication dosages.
2. **No Hardware Alterations:** The system strictly refuses instructions to alter ventilator/concentrator oxygen flow, override hardware limits, or silence/disable safety alarms.
3. **Emergency Handoff:** Safety-critical queries immediately trip the `MEDICAL_SAFETY_TRIAGE` guardrail, returning an emergency clinical disclaimer and creating a high-priority human review ticket.

---

## 5. Quickstart & Installation

The application runs entirely local-first without requiring any paid API keys (`MOCK_LLM=true` default).

### Prerequisites
- Python 3.11+ (tested on Python 3.13)
- Node.js 18+ & npm (for frontend compilation)
- Git

### 1. Clone & Set Up Python Environment
```powershell
# Clone the repository
git clone https://github.com/your-username/medantrik-assist-capstone.git
cd medantrik-assist-capstone

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate.bat

# Install backend dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Build the React Frontend
```powershell
cd frontend
npm install
npm run build
cd ..
```
The compiled production bundle is placed into `frontend/dist/` and automatically served by FastAPI.

### 3. Run Verification & Test Suites
```powershell
# 1. Run the master acceptance verification runner (validates all 16 tasks)
python -m scripts.run_final_verification

# 2. Run the complete pytest test suite (57 passing tests)
python -m pytest -q
```

### 4. Launch the Full-Stack Application
You can launch the complete application with a single command:
```powershell
# Windows single-port launch script (starts backend and opens http://localhost:8000)
.\run_all.bat
```
Or run directly via Uvicorn:
```powershell
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to access the full interactive interface.

---

## 6. Frontend Features & User Experience

The frontend is a single-port React 18 + TypeScript application styled with custom CSS:

- **Overview Dashboard:** Live respiratory wave visualization, metric tiles, recent ticket status table, and product-aware quick-launch cards for OxySense, NODex, and Iron Lung.
- **Conversations (Chat):** Multi-session conversation management, live WebSocket streaming with real-time agent execution stages, quick starter prompts, guardrail pills, citation pills, and an **Evidence Drawer** distinguishing verified facts from demo policies.
- **Ticket Management:** Filter by category, status, and search query. Interactive ticket detail drawer with audit event timeline and human reviewer resolve/reject controls.
- **Knowledge Base:** Dual-pane documentation explorer separating official product specs from the 12 synthetic operational policies.
- **Analytics & Governance:** Visualizations of ticket status/category distributions, RAG calibration separation margins, and the 15-case LLM-judge benchmark table.
- **Language Switcher:** English / Hindi basic interface localization toggle.

---

## 7. Project Directory Structure

```text
chat_support_system_capstone/
├── api/                        # FastAPI backend & WebSocket server
│   ├── app.py                  # API endpoints, WebSocket handler, static mounting
│   ├── logging.py              # Structured JSONL masked logger
│   └── models.py               # Pydantic HTTP & WS schemas
├── database/                   # SQLite schema, migrations & escalation scoring
│   └── db.py                   # Thread-safe SQLite database manager
├── data/                       # Seed dataset & verified public catalog
│   ├── product_catalog.json    # Verified Medantrik product facts
│   └── seed_tickets.json       # 80 deterministically seeded tickets
├── docs/                       # Architectural & design specifications
│   ├── ACCEPTANCE_MATRIX.md    # 16-task acceptance criteria
│   ├── ARCHITECTURE.md         # Full system architecture
│   ├── BUILD_PHASES.md         # Phased implementation log
│   └── DESIGN_SPEC.md          # Visual and UX design tokens
├── evidence/                   # Measured verification evidence
│   ├── calibration.json        # Empirical RAG calibration measurements
│   ├── cache_hit.json          # Policy caching test proof
│   ├── crew_calls.json         # CrewAI kickoff & tool event logs
│   ├── dataset_report.json     # Seed dataset statistics
│   ├── evaluation_results.json # 15-case LLM judge benchmark
│   ├── index_stats.json        # Chroma collection chunk metrics
│   ├── masked_logs.jsonl       # Masked JSONL audit log sample
│   ├── memory_transcripts.json # LangChain session isolation proof
│   ├── retrieval_comparison.md # RAG chunking evaluation report
│   ├── review_cases.json       # AutoGen approve/revise case proof
│   └── screenshots/            # Desktop (1440x900) & mobile (390x844) PNGs
├── frontend/                   # React 18 + TypeScript + Vite SPA
│   ├── src/                    # Components, views, types, api client
│   └── dist/                   # Production build mounted on /
├── knowledge_base/             # 12 original synthetic demo policies
├── rag/                        # ChromaDB vector store & embeddings
│   ├── calibration.py          # Similarity calibration runner
│   ├── chunking.py             # Fixed-overlap & sentence chunkers
│   ├── config.py               # Chroma paths & model configurations
│   ├── core.py                 # Embedding engine & retrieval functions
│   └── evaluation.py           # Precision & recall benchmark
├── scripts/                    # Verification & indexing automation
│   ├── capture_screenshots.py  # Headless browser screenshot generator
│   ├── generate_crew_evidence.py # CrewAI evidence logger
│   ├── rebuild_indexes.py      # Chroma collection builder
│   └── run_final_verification.py # Master 16-task acceptance runner
├── support/                    # Agent orchestration, safety & governance
│   ├── cache.py                # Semantic policy response cache
│   ├── crew.py                 # CrewAI 3-agent orchestration & mock LLM
│   ├── governance.py           # Token budget & risk classification
│   ├── guardrails.py           # PII masking, injections & medical safety
│   ├── models.py               # Pydantic support response schemas
│   ├── review.py               # AutoGen 2-agent compliance group chat
│   ├── runtime.py              # Offline HuggingFace cache configuration
│   ├── session.py              # LangChain session history management
│   └── tickets.py              # Ticket lookup tool & escalation scoring
├── tests/                      # 57 passing automated unit & integration tests
├── .env.example                # Safe environment variable template
├── .gitignore                  # Git exclusion rules
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
├── run_all.bat                 # One-click Windows launch script
├── run_backend.bat             # FastAPI backend launch script
└── run_ui.bat                  # Vite dev launch script
```

---

## 8. Git Hygiene & Submission Verification

All runtime caches, virtual environments, local model weights, and database artifacts are excluded from git tracking via `.gitignore`:
- `*.db` / `*.sqlite`
- `.runtime/` / `.cache/`
- `.venv/` / `__pycache__/`
- `node_modules/` / `frontend/node_modules/`
- `.env` (secrets excluded; safe template in `.env.example`)

---

## 9. License & Academic Integrity Notice

This project is created strictly as an educational capstone demonstration. All product names, logos, and brands are property of their respective owners. Medantrik Medtech Pvt. Ltd. does not endorse, sponsor, or operate this prototype. No patient health records or confidential company data were accessed or utilized.
