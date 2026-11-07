# Requirements traceability — do not claim passed without executing tests

The reference is a 100-mark / 16-task **Ola-specific** problem statement. Maintain its **technical** benchmark while making Medantrik the original simulated domain. An official separate Chat Support System brief, if issued, takes precedence.

| Task | Required acceptance evidence | Location |
|---|---|---|
| 1 Dataset | ≥40 seeded tickets, category ≥3, all statuses, 10–30% escalated, printed counts and seed | `dataset.py`, `evidence/dataset_report.json` |
| 2 Knowledge | ≥12 ORIGINAL 2–5 sentence demo policies on required 12 topics | `knowledge_base/*.md` |
| 3 Chunking | Two independently embedded Chroma collections: overlapping fixed + sentences | `rag/chunking.py`, `scripts/rebuild_indexes.py`, `evidence/index_stats.json` |
| 4 Grounding | Five in-domain, one out-of-domain test; similarity threshold derived from ≥3 in/≥2 out measurements | `rag/calibration.py`, `evidence/calibration.json`, RAG transcript |
| 5 Retrieval eval | Document-level precision and recall per query for BOTH indexes, detailed fractions and recommendation | `rag/evaluation.py`, `evidence/retrieval_comparison.md` |
| 6 Ticket lookup | `check_support_ticket_status` returns real synthetic fixture, status, hours, scored escalation in [0,1] | `support/tickets.py`, `tests/test_ticket_tool.py` |
| 7 CrewAI | Three actual CrewAI agents; `crew.kickoff()` succeeds; RAG and ticket lookup tool calls observable | `support/crew.py`, `evidence/crew_calls.json` |
| 8 Session memory | LangChain session history in same process; follow-up resolves prior ticket; fresh session does not | `support/session.py`, `evidence/memory_transcripts.json` |
| 9 Structured responses | Strict validated Pydantic model for EVERY actual crew result | `support/models.py`, validation tests |
| 10 Guardrails | Phone masking before memory/logs, prompt-injection block, output groundedness fallback, deliberate negative tests | `support/guardrails.py`, `tests/test_guardrails.py` |
| 11 API and socket | ≥2 HTTP routes, typed contracts, functioning WebSocket, graceful disconnect and subsequent client | `api/app.py`, `tests/test_api.py`, `tests/test_websocket.py` |
| 12 Logs | Exactly one JSONL per request with trace id/time; no unmasked demo phone | `api/logging.py`, `evidence/masked_logs.jsonl` |
| 13 Judge | 15 original test cases covering all 12 policy topics + 2 negative, four scores per case + four averages | `evaluation/`, `evidence/evaluation_results.json` |
| 14 AutoGen | Two actual AutoGen agents in RoundRobinGroupChat; structured verdict; approve AND revise proven | `support/review.py`, `evidence/review_cases.json` |
| 15 Governance | Only Lookup Agent has ticket tool; justified High-risk medical-adjacent classification; token/cost cap rejects request | `support/governance.py`, test evidence |
| 16 Cache | Cache same normalized grounded policy query; prove no repeated expensive call; never cache private ticket result across sessions | `support/cache.py`, `evidence/cache_hit.json` |
| Submission | Single PUBLIC GitHub repo, self-contained README, no API keys, transcripts, demo UI, reproducible setup | `README.md`, checked public repo URL |

## Additional features, only after all 16 tasks work
- Clinically cautious safety triage that defaults to human review.
- Distinguishable evidence provenance drawer: VERIFIED PUBLIC vs DEMO POLICY.
- Live synthetic ticket status timeline with audit events and human decision.
- Product-aware follow-up cards for OxySense / NODex / Iron Lung.
- Analytics that correctly labels measured vs simulated metrics.
- English/Hindi interface toggle for basic UI labels; do not advertise bilingual natural-language model fluency without tests.
