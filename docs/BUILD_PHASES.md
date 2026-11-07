# Execute in Anti-Gravity — staged prompts, in order

**Method:** Give the master prompt first. Issue ONE phase prompt at a time, wait for actual file changes and executed tests, verify, then continue. Avoid a single unverified “build everything” response.

## Phase 0 — inspect and plan
"Read START_HERE.md, ANTI_GRAVITY_MASTER_PROMPT.md, docs/ACCEPTANCE_MATRIX.md, docs/MEDANTRIK_RESEARCH.md, docs/DESIGN_SPEC.md, docs/ARCHITECTURE.md and reference/REFERENCE_CAPSTONE_PROBLEM_STATEMENT.md. Inspect the read-only Ola project if attached. Show the planned NEW repository tree and a 16-task implementation mapping. Do not copy Ola code or create fake test results. Then immediately scaffold the project and continue with Phase 1."

## Phase 1 — core data & knowledge
"Create a brand-new repo `medantrik-assist-capstone` with the agreed layout; bring over the seed dataset and original 12 synthetic policy docs. Implement dataset validation and actual tests. Write report values (seed 20261107, 80 tickets, category/status counts and 17.5% escalated) by executing `python dataset.py`. Include public company product facts in a separately labelled indexed corpus. Build an SQLite demo ticket and audit schema. Do not use real customer data. Run pytest; print file tree, commands and results."
**Gate:** determinism test, min counts, status counts, escalated band; 12 docs each 2–5 sentences; SQLite schema initialized.

## Phase 2 — RAG/threshold/eval
"Implement real SentenceTransformers embeddings and two distinct persistent Chroma collections. Use fixed chunks with overlap and sentence chunks, preserve source metadata and type. Run at least three supported and two unsupported calibration questions to measure actual similarity, derive thresholds between clusters, and log chosen values (do not use hardcoded 0.5, 0.6, etc.). Test five in-scope policy questions and one truly unrelated question, then compute parent-document precision/recall for both indexes with explicit TP/FP/FN fractions, and recommend from measured results. Save JSON/MD proof under evidence."
**Gate:** actual non-empty collections, measurements and citations; out-of-domain fallback.

## Phase 3 — CrewAI, memory, guards, review
"Use actual CrewAI agents (Retrieval, Ticket Lookup, Response Composer) and `crew.kickoff()`, not a hand-written class named Crew. Keep only Lookup Agent authorized to read ticket data. Implement deterministic keyless `MOCK_LLM=true` by extending CrewAI BaseLLM; disable telemetry before import; avoid brittle ReAct parsing or tool-name dispatch. Add LangChain per-session memory and strict Pydantic outputs. Mask Indian mobile numbers before histories, logs and tools; block prompt injections, enforce output evidence grounding; add medical-safety escalation. Implement true AutoGen two-agent RoundRobinGroupChat (max_turns=2; register structured message type for verdict) and show both approve and revise cases. Keep it honest: if dependency APIs differ, read installed version docs and adapt, then run it."
**Gate:** real kickoff tool traces; two-session isolation; guardrail triggers; real AutoGen structured verdicts.

## Phase 4 — backend, observability, governance
"Build FastAPI typed POST /ask and /reset-session plus WebSocket /ws/chat and optional GET tickets/metrics endpoints. Persist synthetic tickets and audit records. Log exactly one masked JSONL per call with trace id and latency. Handle WebSocketDisconnect. Enforce 50k simulated token / $0.10 simulated budget, demonstrate rejection on oversize input and report zero real API spend. Cache policy answers only, count tool calls, show true cache hit; never cache ticket-specific or clinical advice. Implement at least 15 explicit mock judge cases with four scores each and averages, and document medically adjacent HIGH risk (not Low because sensitive health context)."
**Gate:** API tests, socket disconnect test, no raw PII, cache counter evidence, runtime-budget negative tests, judge output.

## Phase 5 — premium interface, integrate
"Build the React + TypeScript frontend around design_preview/index.html and docs/DESIGN_SPEC.md. The HTML is only a quality reference. Replace mock responses with typed API and WebSocket; build Overview, Conversations, Tickets, Knowledge and Analytics. Implement evidence drawer, source-type chips, escalation CTA, multi-session chat, search/filter tickets, live metrics and auditing. Never hardcode claimed backend stats or pretend an escalation reached real Medantrik. Responsive mobile layout, keyboard behavior, accessible contrast, polished empty/error/loading states, local seeded sample questions. Capture 1440x900 and 390x844 screenshots and inspect them."
**Gate:** customer chat actually receives backend response; ticket lookup + escalation display; disconnected/empty UI; visually polished screenshots; browser console free of errors.

## Phase 6 — full submission QA
"Execute `python -m pytest -q` (or project equivalent), real CLI RAG/crew/review demos, `python -m scripts.run_final_verification`, and FastAPI HTTP/WS smoke tests. Generate or refresh evidence files from these runs; do not manufacture test scores. Write a clear README with exact commands, seed/weights/amount ranges, measured threshold, numbers for precision/recall, screenshots (optional), limitations, design features, safety and all 16 task proofs. Use `git status` to ensure secrets, model weights, Chroma runtime files, logs, SQLite and cache are ignored. Create a clean final commit and provide GitHub CLI commands / steps to push PUBLIC repo. Only say 'ready to submit' if all acceptance gates pass."
**Gate:** 16 tasks pass with evidence, README reproducible, public repo opened to verify.

## If a phase fails
Do not proceed to unrelated UI changes. Show the actual traceback, root cause, exact files changed and rerun the failing commands. Never mask a broken requirement with a hardcoded response, fabricated screenshot or simulated test result.
