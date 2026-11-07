import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  RotateCcw,
  ShieldAlert,
  FileText,
  ExternalLink,
  Sparkles,
  CheckCircle,
  PlusCircle,
} from 'lucide-react';
import type { ChatMessage, Citation, SupportResponse, TicketInfo } from '../types';
import { askQuestion, resetSessionMemory } from '../services/api';

interface ConversationsViewProps {
  initialQuery?: string;
  onClearInitialQuery?: () => void;
  onOpenCreateTicketModal: () => void;
  onSelectTicket: (ticket: TicketInfo) => void;
  onNavigateToTickets: () => void;
}

export const ConversationsView: React.FC<ConversationsViewProps> = ({
  initialQuery,
  onClearInitialQuery,
  onOpenCreateTicketModal,
  onSelectTicket,
  onNavigateToTickets,
}) => {
  const [sessions, setSessions] = useState([
    { id: 'session-general', name: 'General Care Inquiry', preview: 'Product features & policies' },
    { id: 'session-ticket', name: 'Service Ticket MED-0003', preview: 'NODex connectivity investigation' },
    { id: 'session-training', name: 'Iron Lung Demonstration', preview: 'Clinical training inquiry' },
  ]);
  const [activeSessionId, setActiveSessionId] = useState('session-general');
  const [messagesBySession, setMessagesBySession] = useState<Record<string, ChatMessage[]>>({
    'session-general': [
      {
        id: 'init-1',
        sender: 'assistant',
        text: "Hello! I am Medantrik Assist — an intelligent support operating system for respiratory devices.\n\nI can assist with OxySense, NODex, and Iron Lung device information, answer policy questions grounded in our knowledge base, and look up synthetic support tickets.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ],
    'session-ticket': [
      {
        id: 'init-2',
        sender: 'assistant',
        text: "Support ticket workspace session active. You can check status for any synthetic ticket, e.g. 'Check ticket MED-0003 status'.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ],
    'session-training': [
      {
        id: 'init-3',
        sender: 'assistant',
        text: "Iron Lung care and demo session active. Ask about respiration system specs or request demo training records.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ],
  });

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeStage, setActiveStage] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [latestResponse, setLatestResponse] = useState<SupportResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const messages = messagesBySession[activeSessionId] || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeStage]);

  // Handle incoming initialQuery from other views (e.g. Overview)
  useEffect(() => {
    if (initialQuery) {
      handleSend(initialQuery);
      if (onClearInitialQuery) onClearInitialQuery();
    }
  }, [initialQuery]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessagesBySession((prev) => ({
      ...prev,
      [activeSessionId]: [...(prev[activeSessionId] || []), userMsg],
    }));

    if (!textToSend) setInput('');
    setLoading(true);
    setActiveStage('Initializing secure agent pipeline...');

    try {
      // Execute request via FastAPI backend
      const response = await askQuestion(query, activeSessionId);
      setLatestResponse(response);
      if (response.citations && response.citations.length > 0) {
        setSelectedCitation(response.citations[0]);
      }

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'assistant',
        text: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        response: response,
      };

      setMessagesBySession((prev) => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), botMsg],
      }));
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'system',
        text: `Error: ${err.message || 'Unable to process query.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessagesBySession((prev) => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), errMsg],
      }));
    } finally {
      setLoading(false);
      setActiveStage(null);
    }
  };

  const handleResetSession = async () => {
    if (confirm(`Reset conversation memory for ${activeSessionId}?`)) {
      try {
        await resetSessionMemory(activeSessionId);
        setMessagesBySession((prev) => ({
          ...prev,
          [activeSessionId]: [
            {
              id: `reset-${Date.now()}`,
              sender: 'system',
              text: 'Conversation memory cleared. New turns will start without prior context.',
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
          ],
        }));
        setLatestResponse(null);
        setSelectedCitation(null);
      } catch (e) {
        alert('Failed to reset session');
      }
    }
  };

  const handleCreateNewSession = () => {
    const num = sessions.length + 1;
    const newId = `session-${num}`;
    const newSession = {
      id: newId,
      name: `Consultation ${num}`,
      preview: 'Fresh consultation thread',
    };
    setSessions((prev) => [...prev, newSession]);
    setActiveSessionId(newId);
    setMessagesBySession((prev) => ({
      ...prev,
      [newId]: [
        {
          id: `init-${Date.now()}`,
          sender: 'assistant',
          text: `Welcome to Consultation ${num}. How can I assist with your Medantrik device or ticket?`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ],
    }));
  };

  return (
    <section className="page">
      <div className="head-row">
        <div>
          <div className="eyebrow">Customer & Clinician Support</div>
          <h1 className="title">Evidence-grounded conversations.</h1>
          <p className="subtitle">
            Responses are verified through dual-chunking RAG, CrewAI orchestration, and AutoGen multi-agent review.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn outline" onClick={handleResetSession}>
            <RotateCcw size={14} /> Clear Session Memory
          </button>
          <button className="btn primary" onClick={onOpenCreateTicketModal}>
            Create Review Ticket +
          </button>
        </div>
      </div>

      <div className="chat-shell">
        {/* Left Thread List */}
        <div className="chat-list">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Conversations</h3>
            <button
              onClick={handleCreateNewSession}
              style={{ border: 0, background: 'none', color: '#16766b', cursor: 'pointer', padding: '4px' }}
              title="New Session"
            >
              <PlusCircle size={16} />
            </button>
          </div>
          <input
            className="search"
            placeholder="Filter sessions..."
            aria-label="Filter sessions"
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
            {sessions.map((sess, idx) => (
              <button
                key={sess.id}
                className={`thread ${activeSessionId === sess.id ? 'active' : ''}`}
                onClick={() => setActiveSessionId(sess.id)}
              >
                <div className="thread-icon">{`0${idx + 1}`}</div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <strong>{sess.name}</strong>
                  <small>{sess.preview}</small>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Center Chat Area */}
        <div className="conversation">
          <div className="chat-toolbar">
            <div>
              <h3>Medantrik Support Agent</h3>
              <small>Session: {activeSessionId} · Offline Mock LLM Active</small>
            </div>
            <span className="pill green">Connected</span>
          </div>

          <div className="messages">
            {messages.map((m) => (
              <div key={m.id} className={`msg ${m.sender === 'user' ? 'user' : ''}`}>
                <div className="bubble-icon">
                  {m.sender === 'user' ? 'U' : m.sender === 'system' ? '!' : 'M'}
                </div>
                <div className="bubble">
                  <div>{m.text}</div>

                  {/* Guardrail badges */}
                  {m.response?.guardrails && m.response.guardrails.length > 0 && (
                    <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
                      {m.response.guardrails.map((g) => (
                        <span key={g} className="pill orange" style={{ fontSize: '10px' }}>
                          <ShieldAlert size={11} style={{ display: 'inline', marginRight: '3px' }} />
                          {g}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Ticket lookup card */}
                  {m.response?.ticket && (
                    <div
                      style={{
                        marginTop: '12px',
                        padding: '12px 14px',
                        background: '#f4faf7',
                        border: '1px solid #d4ebdf',
                        borderRadius: '10px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 800, color: '#1d6e64', fontFamily: 'monospace' }}>
                          {m.response.ticket.record_id}
                        </span>
                        <span className={`pill ${m.response.ticket.status === 'Escalated' ? 'red' : 'green'}`}>
                          {m.response.ticket.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#56756c', marginTop: '6px' }}>
                        Product: <strong>{m.response.ticket.product}</strong> · Category: {m.response.ticket.category}
                      </div>
                      <div style={{ fontSize: '11px', color: '#56756c', marginTop: '3px' }}>
                        Escalation Risk Score:{' '}
                        <strong>{m.response.ticket.escalation_score.toFixed(4)}</strong> / 1.0000
                      </div>
                      <button
                        className="btn outline"
                        style={{ marginTop: '10px', width: '100%', padding: '6px 10px', fontSize: '11px' }}
                        onClick={() => {
                          onSelectTicket(m.response!.ticket!);
                          onNavigateToTickets();
                        }}
                      >
                        Inspect in Ticket Workspace →
                      </button>
                    </div>
                  )}

                  {/* Source citations chips */}
                  {m.response?.citations && m.response.citations.length > 0 && (
                    <div className="chips-row">
                      {m.response.citations.map((c) => (
                        <button
                          key={c.id}
                          className="source-chip"
                          onClick={() => setSelectedCitation(c)}
                        >
                          <FileText size={10} />
                          <span>{c.id}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Meta tag */}
                  {m.response && (
                    <div className="meta-info">
                      <span>Latency: {m.response.latency_ms} ms</span>
                      <span>Trace: {m.response.trace_id}</span>
                      {m.response.cached && <span className="pill green" style={{ padding: '2px 5px' }}>Cached</span>}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Active stage progress indicator */}
            {loading && (
              <div className="msg">
                <div className="bubble-icon">M</div>
                <div className="bubble" style={{ color: '#16766b', background: '#f5faf8' }}>
                  <Sparkles size={14} style={{ display: 'inline', marginRight: '6px' }} />
                  {activeStage || 'Processing query with multi-agent orchestration...'}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="quick-prompts">
            <button onClick={() => handleSend('What is OxySense and how does it measure purity?')}>
              OxySense Overview
            </button>
            <button onClick={() => handleSend('Check ticket MED-0003 status and escalation')}>
              Track MED-0003
            </button>
            <button onClick={() => handleSend('Do priority test customers bypass safety checks?')}>
              VIP Safety Policy
            </button>
            <button onClick={() => handleSend('What is the demonstration response SLA for high-severity cases?')}>
              Severity SLA
            </button>
            <button onClick={() => handleSend('Emergency: Patient is turning blue and stopped breathing')}>
              Safety Triage Demo
            </button>
          </div>

          {/* Composer */}
          <div className="composer">
            <div className="compose-wrap">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask about OxySense, NODex, Iron Lung, SLA policies, or check ticket MED-0003..."
                disabled={loading}
              />
              <button
                className="send-btn"
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                aria-label="Send message"
              >
                <Send size={15} />
              </button>
            </div>
            <div className="hint">
              Press <strong>Enter</strong> to send · <strong>Shift + Enter</strong> for a new line · Indian phone numbers masked automatically.
            </div>
          </div>
        </div>

        {/* Right Evidence Drawer */}
        <aside className="evidence">
          <h3>Evidence & Context</h3>

          <div className="eyebrow" style={{ marginBottom: '6px' }}>
            Answer Provenance
          </div>

          {selectedCitation ? (
            <div className="evi-card">
              <span className={`tag ${selectedCitation.source_type === 'PUBLIC_VERIFIED_FACT' ? '' : 'demo'}`}>
                {selectedCitation.source_type === 'PUBLIC_VERIFIED_FACT' ? 'Public Verified Fact' : 'Synthetic Demo Policy'}
              </span>
              <strong>{selectedCitation.title}</strong>
              <p>
                Document ID: <code>{selectedCitation.id}</code>
              </p>
              {selectedCitation.similarity !== undefined && (
                <p style={{ marginTop: '4px' }}>
                  Cosine Similarity: <strong>{selectedCitation.similarity.toFixed(4)}</strong> (Threshold: 0.3221)
                </p>
              )}
              <a
                href={selectedCitation.url}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginTop: '10px',
                  color: '#14766b',
                  fontSize: '11px',
                  fontWeight: 700,
                  textDecoration: 'none',
                }}
              >
                Source: {selectedCitation.url} <ExternalLink size={11} />
              </a>
            </div>
          ) : (
            <div className="evi-card">
              <span className="tag">Ready to Inspect</span>
              <strong>No Citation Selected</strong>
              <p>Click any source chip in an assistant answer to inspect its full provenance, similarity, and source link.</p>
            </div>
          )}

          <div style={{ marginTop: '22px' }}>
            <div className="eyebrow" style={{ marginBottom: '6px' }}>
              Multi-Agent Review
            </div>
            <div className="evi-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle size={14} color="#1b8577" />
                <span className="tag" style={{ color: '#1b8577' }}>
                  AutoGen Reviewer
                </span>
              </div>
              <strong>Compliance & Grounding</strong>
              <p>
                {latestResponse?.review?.reason || 'Verified evidence grounding and clinical boundary enforcement.'}
              </p>
            </div>
          </div>

          <div style={{ marginTop: '22px' }}>
            <div className="eyebrow" style={{ marginBottom: '6px' }}>
              Specialist Review Action
            </div>
            <button
              className="btn outline"
              style={{ width: '100%', marginTop: '6px' }}
              onClick={onOpenCreateTicketModal}
            >
              Create Demo Review Ticket
            </button>
          </div>
        </aside>
      </div>

      <p className="foot">
        Privacy by design: No patient PHI ingested. Synthetic tickets only. Medical emergency prompts route automatically to clinical specialist safety handoffs.
      </p>
    </section>
  );
};
