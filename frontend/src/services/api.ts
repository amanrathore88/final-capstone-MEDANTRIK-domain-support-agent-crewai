/**
 * API service for Medantrik Assist backend.
 */
import type { KnowledgeData, Metrics, SupportResponse, TicketInfo, AuditEvent } from '../types';

const API_BASE = typeof window !== 'undefined' && window.location.port === '5173' ? 'http://localhost:8000' : '';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function fetchKnowledge(): Promise<KnowledgeData> {
  const res = await fetch(`${API_BASE}/knowledge`);
  if (!res.ok) throw new Error('Failed to fetch knowledge');
  return res.json();
}

export async function fetchTickets(params?: {
  status?: string;
  category?: string;
  search?: string;
  limit?: number;
}): Promise<TicketInfo[]> {
  const q = new URLSearchParams();
  if (params?.status) q.append('status', params.status);
  if (params?.category) q.append('category', params.category);
  if (params?.search) q.append('search', params.search);
  if (params?.limit) q.append('limit', String(params.limit));

  const res = await fetch(`${API_BASE}/tickets?${q.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch tickets');
  return res.json();
}

export async function fetchTicketDetail(recordId: string): Promise<{ ticket: TicketInfo; audit_events: AuditEvent[] }> {
  const res = await fetch(`${API_BASE}/tickets/${recordId}`);
  if (!res.ok) throw new Error(`Ticket ${recordId} not found`);
  return res.json();
}

export async function createTicket(data: {
  category: string;
  severity: string;
  customer_role: string;
  subject: string;
  description: string;
  product_name?: string;
}): Promise<TicketInfo> {
  const res = await fetch(`${API_BASE}/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create ticket');
  return res.json();
}

export async function recordDecision(
  recordId: string,
  decision: string,
  notes: string = '',
  operator: string = 'Human Operator'
): Promise<{ ticket: TicketInfo; audit_events: AuditEvent[] }> {
  const res = await fetch(`${API_BASE}/tickets/${recordId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, notes, operator }),
  });
  if (!res.ok) throw new Error('Failed to record operator decision');
  return res.json();
}

export async function askQuestion(query: string, sessionId: string = 'default'): Promise<SupportResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function resetSessionMemory(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/reset-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error('Failed to reset session memory');
}

export function createWebSocketChat(
  onStage: (stage: string, message: string) => void,
  onResponse: (response: SupportResponse) => void,
  onError: (errorMsg: string) => void
) {
  const host = typeof window !== 'undefined' && window.location.port === '5173' ? 'localhost:8000' : (typeof window !== 'undefined' ? window.location.host : 'localhost:8000');
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${host}/ws/chat`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'stage') {
        onStage(data.stage, data.message);
      } else if (data.type === 'response') {
        onResponse(data.response);
      } else if (data.type === 'error') {
        onError(data.message || 'Server error occurred');
      }
    } catch (e) {
      onError('Failed to parse WebSocket message');
    }
  };

  ws.onerror = () => {
    onError('WebSocket connection error');
  };

  return {
    send: (query: string, sessionId: string) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ query, session_id: sessionId }));
        return true;
      }
      return false;
    },
    close: () => ws.close(),
    isOpen: () => ws.readyState === WebSocket.OPEN,
  };
}
