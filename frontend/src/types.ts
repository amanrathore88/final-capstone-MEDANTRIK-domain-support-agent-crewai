/**
 * TypeScript types for Medantrik Assist Support OS (Phase 5).
 */

export interface Citation {
  id: string;
  title: string;
  source_type: 'SYNTHETIC_DEMO_POLICY' | 'PUBLIC_VERIFIED_FACT';
  url: string;
  similarity?: number;
}

export interface TicketInfo {
  record_id: string;
  category: string;
  status: string;
  resolution_time_hours: number;
  days_since_created: number;
  escalated: boolean;
  product: string;
  reopen_count: number;
  subject: string;
  escalation_score: number;
  recommended_review: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AuditEvent {
  id: number;
  ticket_id: string;
  action: string;
  from_status: string | null;
  to_status: string | null;
  actor: string;
  details: string;
  timestamp: string;
}

export interface SupportResponse {
  answer: string;
  outcome: 'answered' | 'refused' | 'ticket_lookup' | 'not_found' | 'out_of_domain';
  citations: Citation[];
  ticket?: TicketInfo | null;
  guardrails: string[];
  needs_human: boolean;
  trace_id?: string;
  session_id?: string;
  latency_ms?: number;
  cached?: boolean;
  governance?: {
    total_tokens: number;
    total_cost: number;
    external_api_spend: number;
  };
  review?: {
    approved: boolean;
    reason: string;
  };
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  response?: SupportResponse;
  stage?: string;
  loading?: boolean;
}

export interface Metrics {
  total_tickets: number;
  escalated_count: number;
  escalated_percentage: number;
  categories: Record<string, number>;
  statuses: Record<string, number>;
  severities?: Record<string, number>;
}

export interface KnowledgePolicy {
  slug: string;
  title: string;
  provenance: string;
  disclaimer: string;
  content: string;
}

export interface VerifiedProduct {
  id: string;
  name: string;
  kind: string;
  description: string;
  provenance: string;
  source: string;
}

export interface KnowledgeData {
  verified_public: {
    company: Record<string, any>;
    products: VerifiedProduct[];
  };
  synthetic_policies: KnowledgePolicy[];
  governance: {
    level: string;
    domain: string;
    justification: string;
  };
}

export interface EvalCase {
  id: string;
  topic: string;
  kind: string;
  query: string;
  scores: {
    accuracy: number;
    grounding: number;
    completeness: number;
    safety: number;
  };
  average: number;
  latency_ms: number;
}

export interface EvalResults {
  benchmark: string;
  total_cases: number;
  metrics_average: {
    accuracy: number;
    grounding: number;
    completeness: number;
    safety: number;
    overall: number;
  };
  cases: EvalCase[];
}
