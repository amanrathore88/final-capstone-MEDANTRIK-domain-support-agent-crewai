# Reference-grade architecture (to be implemented, not falsely claimed as implemented)

## Repository tree (preserve the Ola reference's recognizable top-level structure, replace implementation)
```
medantrik-assist-capstone/
├── README.md
├── Problem_Statement.md                   # explain selected track; don't label as Ola
├── .gitignore
├── .env.example
├── dataset.py                             # generated from seed_code/dataset.py, own design
├── requirements-api.txt
├── requirements-crew.txt
├── requirements-rag.txt
├── api/
│   ├── app.py                            # FastAPI /health, /ask, /tickets, /reset-session, /ws/chat
│   ├── models.py                         # Pydantic request/response contracts
│   ├── logging.py                        # masked structured JSONL
│   └── offline.py                        # mock runtime, telemetry off
├── support/
│   ├── models.py                         # SupportResponse and TicketResult Pydantic schemas
│   ├── tickets.py                        # dedicated read-only status lookup tool
│   ├── crew.py                           # actual CrewAI 3 agents + kickoff
│   ├── session.py                        # per-session chat history; no leaking between sessions
│   ├── guardrails.py                      # input/PII + evidence & output checking
│   ├── review.py                          # 2-agent AutoGen review with Verdict model
│   ├── governance.py                      # token/cost and autonomy policy
│   ├── cache.py                           # only policy fact responses, not ticket results
│   └── triage.py                          # safety keywords, deterministic routing, safety disclaimer
├── rag/
│   ├── chunking.py                        # fixed-overlap and sentence based
│   ├── core.py                            # SentenceTransformers embeddings & Chroma upsert
│   ├── calibration.py                     # measured threshold, no tutorial constants
│   └── evaluation.py                      # parent-doc precision & recall
├── knowledge_base/                       # 12 synthetic demo policies
├── data/
│   ├── product_catalog.json              # sourced verified public facts
│   └── eval_cases.json                   # 15 original judge cases
├── database/
│   ├── db.py                              # SQLite and migrations for demo tickets only
│   └── schema.sql
├── frontend/
│   ├── src/                               # React + TypeScript + Vite
│   │   ├── app/                           # router, layout, providers
│   │   ├── pages/                         # Overview/Chat/Tickets/Knowledge/Analytics
│   │   ├── components/                    # one reusable component per responsibility
│   │   ├── lib/api.ts                     # typed network client
│   │   ├── hooks/useChatSocket.ts
│   │   └── styles/                        # design tokens + accessible styles
│   ├── package.json
│   └── README.md
├── evaluation/                             # fixture queries + rubrics + per-query results
├── scripts/                                # rebuild-index, ask-support, evaluate, verify-all
├── tests/                                  # pytest deterministic, guardrail, API, websocket, review
├── evidence/                               # clean text/json test transcripts (no giant duplicate archives)
└── docs/                                   # architecture, governance, test report, screenshot notes
```

## Request pipeline
```
Customer UI -> POST /ask or WS /ws/chat
  -> Validate Pydantic inputs
  -> Input guard: mask phone, block prompt injection, budget size
  -> Session history (only already masked content)
  -> Safety triage: suspected clinical/emergency/device safety issue -> safe non-clinical guidance + human ticket
  -> Intent router:
     -> Ticket ID? Lookup Agent: read-only ticket dataset or SQLite lookup, permission checked
     -> Public product/policy question? Retrieval Agent -> SentenceTransformers -> Chroma fixed top-k
  -> CrewAI Retrieval Agent + Lookup Agent + Composer Agent .kickoff()
  -> Pydantic SupportResponse validation
  -> AutoGen RoundRobinGroupChat (Policy Reviewer + Final Editor) -> Verdict
  -> Output grounding/sensitive content guard
  -> Mask again -> JSONL audit with trace_id/duration and no raw phone
  -> Response with answer, sources, ticket, decision, trace_id
  -> UI source drawer, ticket timeline, confidence badge
```

## Isolation & source trust
The searchable store has two distinct source families: **PUBLIC_VERIFIED_FACT** and **SYNTHETIC_DEMO_POLICY**. Always display the family and link to sources; never blend synthetic policies into public-company facts. A fixed-format phone number is masked **before** memory, caching, RAG, logs or network calls. The Lookup Agent tool is not attached to other agents. No actual patient data. Ticket lookup must not expose private users' real records; dataset is fabricated.

## Escalation score (original, auditable)
`score = round(0.50*int(escalated) + 0.30*(days_since_created/30) + 0.20*(reopen_count/3), 6)`.
For provided seed `20261107`, the nearest-rank 80th percentile of the 80 score values is **0.366667**; recommend review if `score > 0.366667`. This routes 16/80 tickets (20%) for review according to the proposed heuristic, separate from **mandatory safety escalation**, which bypasses the score. Recompute if data generation changes and include proof in tests.

## API contracts (recommended additions to required endpoints)
- `GET /health` -> runtime mode, indexed count, version (no sensitive detail).
- `POST /ask` `{"session_id":"demo-01","query":"What does OxySense do?"}` -> `{"trace_id":...,"session_id":...,"response":{"answer":...,"outcome":"answered|partial|not_found|clarification|refused|escalated","citations":[{"id":...,"source_type":...,"url":...}],"ticket":null,"guardrails":[]},"review":{"approved":true,"reason":...}}`.
- `POST /reset-session` `{"session_id":"demo-01"}` -> confirmed reset.
- `GET /tickets` & `GET /tickets/{record_id}` -> fabricated dataset plus demo-owned tickets only.
- `POST /tickets` -> create synthetic ticket, severity/intent, audit event and safe ID. **Never claim official ticket creation**.
- `POST /tickets/{id}/decision` -> fake operator role only, auditable approved/rejected status transitions; do not perform payments.
- `GET /knowledge` -> docs and citations, showing public versus fictional policies distinctly.
- `GET /metrics` -> actual metrics, never hardcoded.
- `WS /ws/chat?session_id=<id>` -> `message`/`answer`/`error` event contracts, graceful WebSocketDisconnect, reconnect handling.

## Prototype persistence and modes
- Default `MOCK_LLM=true`. Deterministic adapter, no API key, no paid model, no network required **after initial dependency/model install**; telemetry disabled before CrewAI import.
- Offline corpus can be reindexed locally after model download; index artifacts are gitignored and created via setup script.
- SQLite for synthetic user-created ticket updates + audit events; original generated tickets can seed the database.
- Avoid pretending that mock intent detection or keyword matching is an ML confidence score.
- Feature-flag optional online LLM only after all keyless tests pass (not needed for grading).

## Failure states
Empty KB -> explicit unavailable; missing model/index -> setup warning; unknown ticket -> not_found with no fake details; unsupported medical question -> refused + human escalation; budget exceeded -> rejected; review failed -> deterministic refusal; WebSocket disconnect -> continue to serve other clients; missing credentials -> mock mode works.
