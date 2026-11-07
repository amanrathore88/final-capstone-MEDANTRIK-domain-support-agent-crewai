# Retrieval Strategy Evaluation & Comparison (Task 5)

## Evaluation Setup
- **Embedding Model:** `all-MiniLM-L6-v2` (384-dimensional cosine space)
- **Top-K:** 3 chunks retrieved per query
- **Parent Document Mapping:** Retrieved chunk IDs are mapped to parent document slugs and deduplicated.
- **Empirical Thresholds:**
  - `fixed_overlap`: **0.3221**
  - `sentence_based`: **0.3231**

## Per-Query Results: Fixed-Overlap Strategy
| Query ID | Expected Parent | Retrieved Parents | TP / FP / FN | Precision | Recall | Top-1 Similarity |
|---|---|---|---|---|---|---|
| q1 | `07_repeat_complaints` | `07_repeat_complaints, 02_severity_sla, 03_escalation_matrix` | 1/2/0 | 1/3 (0.33) | 1/1 (1.00) | 0.3858 |
| q2 | `10_vip_handling` | `10_vip_handling, 01_ticket_priority` | 1/1/0 | 1/2 (0.50) | 1/1 (1.00) | 0.5302 |
| q3 | `11_outage_communication` | `11_outage_communication, 01_ticket_priority` | 1/1/0 | 1/2 (0.50) | 1/1 (1.00) | 0.6622 |
| q4 | `12_ticket_retention` | `12_ticket_retention, 03_escalation_matrix` | 1/1/0 | 1/2 (0.50) | 1/1 (1.00) | 0.3997 |
| q5 | `08_service_credit` | `08_service_credit, 03_escalation_matrix` | 1/1/0 | 1/2 (0.50) | 1/1 (1.00) | 0.6047 |

## Per-Query Results: Sentence-Based Strategy
| Query ID | Expected Parent | Retrieved Parents | TP / FP / FN | Precision | Recall | Top-1 Similarity |
|---|---|---|---|---|---|---|
| q1 | `07_repeat_complaints` | `02_severity_sla, 03_escalation_matrix, 01_ticket_priority` | 0/3/1 | 0/3 (0.00) | 0/1 (0.00) | 0.4262 |
| q2 | `10_vip_handling` | `10_vip_handling, 01_ticket_priority` | 1/1/0 | 1/2 (0.50) | 1/1 (1.00) | 0.5426 |
| q3 | `11_outage_communication` | `11_outage_communication` | 1/0/0 | 1/1 (1.00) | 1/1 (1.00) | 0.5170 |
| q4 | `12_ticket_retention` | `11_outage_communication, 12_ticket_retention, 09_feedback` | 1/2/0 | 1/3 (0.33) | 1/1 (1.00) | 0.4501 |
| q5 | `08_service_credit` | `08_service_credit, 03_escalation_matrix` | 1/1/0 | 1/2 (0.50) | 1/1 (1.00) | 0.5315 |

## Out-of-Scope Fallback Verification
- Query: *"Explain the general theory of relativity and black holes in spacetime"*
- `fixed_overlap`: Top-1 similarity = **0.1273** (Threshold = 0.3221) → Fallback Triggered: **True**
- `sentence_based`: Top-1 similarity = **0.1348** (Threshold = 0.3231) → Fallback Triggered: **True**

## Strategy Comparison & Recommendation
| Metric | Fixed-Overlap Chunking | Sentence-Based Chunking |
|---|---|---|
| **Total Chunks** | 33 | 60 |
| **Mean Document Precision** | **0.4667** | **0.4667** |
| **Mean Document Recall** | **1.0000** | **0.8000** |
| **F1 Score** | **0.6364** | **0.5895** |
| **Out-of-Scope Separation Margin** | **0.3186** | **0.2357** |

### Deployment Recommendation
We recommend deploying the **`fixed_overlap`** chunking strategy for the Medantrik Assist customer support pipeline. While sentence-based chunking achieves competitive retrieval, fixed-overlap chunking delivers a superior cluster separation margin (0.3186 vs 0.2357) and provides richer surrounding operational context (F1 = 0.6364) without splitting cross-sentence policy qualifications.
