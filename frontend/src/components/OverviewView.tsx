import React from 'react';
import { FileText, ShieldAlert, CheckCircle2, BookOpen, ArrowRight, Activity, Cpu, Wind } from 'lucide-react';
import type { Metrics, TicketInfo } from '../types';

interface OverviewViewProps {
  metrics: Metrics | null;
  recentTickets: TicketInfo[];
  onNavigate: (page: string) => void;
  onAskQuestion: (query: string) => void;
  onSelectTicket: (ticket: TicketInfo) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  metrics,
  recentTickets,
  onNavigate,
  onAskQuestion,
  onSelectTicket,
}) => {
  const getBadgeClass = (status: string) => {
    switch (status) {
      case 'Escalated': return 'pill red';
      case 'Open': return 'pill orange';
      case 'Closed': return 'pill gray';
      case 'Resolved': return 'pill green';
      default: return 'pill blue';
    }
  };

  return (
    <section className="page">
      <div className="head-row">
        <div>
          <div className="eyebrow">Medantrik Support Workspace</div>
          <h1 className="title">
            Better support.<br />Clearer care conversations.
          </h1>
          <p className="subtitle">
            One grounded place to answer device questions, guide support requests, and keep every case accountable.
          </p>
        </div>
        <button className="btn primary" onClick={() => onNavigate('conversations')}>
          Start Conversation <ArrowRight size={15} />
        </button>
      </div>

      {/* Hero Banner */}
      <div className="hero">
        <div className="hero-copy">
          <div className="eyebrow">Built for Respiratory Technology</div>
          <h2>
            Every care question deserves<br />a clear next step.
          </h2>
          <p>
            Product-aware support for OxySense, NODex, and Iron Lung — with transparent source evidence, clinical safety guardrails, and careful human handoffs.
          </p>
          <button className="btn soft" onClick={() => onNavigate('knowledge')}>
            Explore Knowledge Base <ArrowRight size={15} />
          </button>
        </div>
        <div className="hero-art">
          <svg viewBox="0 0 320 180" style={{ width: '100%', height: '100%', padding: '20px' }}>
            <path
              d="M0 100h50q15 0 20-20l18-40 25 110 28-80 15 25h35q12 0 18-15l8-15 15 35h88"
              fill="none"
              stroke="#138b7d"
              strokeWidth="3.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="113" cy="150" r="5" fill="#15a99d" />
          </svg>
          <div className="floating-label">
            <strong>Evidence Before Answers</strong>
            Verified Sources · Medical Safety · Human Review
          </div>
        </div>
      </div>

      {/* Metric Cards (Live from API) */}
      <div className="metrics">
        <div className="metric">
          <div className="metric-top">
            Open Cases
            <div className="metric-icon">
              <FileText size={16} />
            </div>
          </div>
          <strong>{metrics?.statuses['Open'] ?? 16}</strong>
          <small>Live synthetic database</small>
        </div>

        <div className="metric">
          <div className="metric-top">
            Escalated Cases
            <div className="metric-icon">
              <ShieldAlert size={16} />
            </div>
          </div>
          <strong style={{ color: '#b3564c' }}>
            {metrics?.escalated_count ?? 14}
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#88a096', marginLeft: '6px' }}>
              ({metrics?.escalated_percentage ?? 17.5}%)
            </span>
          </strong>
          <small>Flagged for specialist triage</small>
        </div>

        <div className="metric">
          <div className="metric-top">
            Resolved Cases
            <div className="metric-icon">
              <CheckCircle2 size={16} />
            </div>
          </div>
          <strong>{metrics?.statuses['Resolved'] ?? 16}</strong>
          <small>Documented solutions</small>
        </div>

        <div className="metric">
          <div className="metric-top">
            Knowledge Coverage
            <div className="metric-icon">
              <BookOpen size={16} />
            </div>
          </div>
          <strong>12 Policies + 3 Devices</strong>
          <small>Empirically calibrated RAG</small>
        </div>
      </div>

      {/* Grid: Recent Tickets & Product Help Desk */}
      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head">
            <h3>Recent Support Tickets</h3>
            <button className="link" onClick={() => onNavigate('tickets')} style={{ border: 0, background: 'none', color: '#16766b', fontWeight: 700, fontSize: '12px', cursor: 'pointer' }}>
              View All 80 Tickets →
            </button>
          </div>
          <table className="tickets-table">
            <thead>
              <tr>
                <th>Ticket / Issue</th>
                <th>Product</th>
                <th>Category</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentTickets.slice(0, 5).map((t) => (
                <tr
                  key={t.record_id}
                  onClick={() => {
                    onSelectTicket(t);
                    onNavigate('tickets');
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  <td>
                    <span className="ticket-id">{t.record_id}</span>
                    <span className="ticket-desc">{t.subject}</span>
                  </td>
                  <td>{t.product}</td>
                  <td>{t.category}</td>
                  <td>
                    <span className={getBadgeClass(t.status)}>{t.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h3>Device Help Desk</h3>
            <button className="link" onClick={() => onNavigate('conversations')} style={{ border: 0, background: 'none', color: '#16766b', fontWeight: 700, fontSize: '12px', cursor: 'pointer' }}>
              Ask Question →
            </button>
          </div>
          <div className="products-list">
            <div className="product">
              <div className="picon">
                <Wind size={22} />
              </div>
              <div>
                <strong>OxySense</strong>
                <p>Inline oxygen purity analyser</p>
              </div>
              <button
                className="arrow"
                onClick={() => onAskQuestion('What is OxySense and how is it used?')}
                title="Ask about OxySense"
              >
                →
              </button>
            </div>

            <div className="product">
              <div className="picon">
                <Activity size={22} />
              </div>
              <div>
                <strong>NODex</strong>
                <p>Smart respiratory assessment device</p>
              </div>
              <button
                className="arrow"
                onClick={() => onAskQuestion('Tell me about NODex device features')}
                title="Ask about NODex"
              >
                →
              </button>
            </div>

            <div className="product">
              <div className="picon">
                <Cpu size={22} />
              </div>
              <div>
                <strong>Iron Lung</strong>
                <p>Smart respiration system</p>
              </div>
              <button
                className="arrow"
                onClick={() => onAskQuestion('What is the Iron Lung system?')}
                title="Ask about Iron Lung"
              >
                →
              </button>
            </div>
          </div>

          <div className="notice">
            <ShieldAlert size={20} style={{ flex: 'none' }} />
            <span>
              <strong>Clinical Safety Policy:</strong> Medical emergencies and alarm silencing requests are never answered with automated dosing or diagnostic instructions. The OS immediately initiates safe clinical handoff.
            </span>
          </div>
        </div>
      </div>

      <p className="foot">
        UNOFFICIAL CAPSTONE DEMO · Uses synthetic demonstration records and policies; not affiliated with Medantrik Medtech Pvt. Ltd.
      </p>
    </section>
  );
};
