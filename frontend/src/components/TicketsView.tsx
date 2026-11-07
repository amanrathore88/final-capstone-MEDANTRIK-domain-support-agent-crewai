import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import type { TicketInfo, AuditEvent } from '../types';
import { recordDecision } from '../services/api';

interface TicketsViewProps {
  tickets: TicketInfo[];
  selectedTicket: TicketInfo | null;
  auditEvents: AuditEvent[];
  onSelectTicket: (ticket: TicketInfo) => void;
  onOpenCreateModal: () => void;
  onRefreshTickets: () => void;
}

export const TicketsView: React.FC<TicketsViewProps> = ({
  tickets,
  selectedTicket,
  auditEvents,
  onSelectTicket,
  onOpenCreateModal,
  onRefreshTickets,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [operatorNotes, setOperatorNotes] = useState('');
  const [acting, setActing] = useState(false);

  const filteredTickets = tickets.filter((t) => {
    const matchesStatus = !statusFilter || t.status === statusFilter;
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      !term ||
      t.record_id.toLowerCase().includes(term) ||
      t.subject.toLowerCase().includes(term) ||
      t.product.toLowerCase().includes(term) ||
      t.category.toLowerCase().includes(term);
    return matchesStatus && matchesSearch;
  });

  const getBadgeClass = (status: string) => {
    switch (status) {
      case 'Escalated': return 'pill red';
      case 'Open': return 'pill orange';
      case 'Closed': return 'pill gray';
      case 'Resolved': return 'pill green';
      default: return 'pill blue';
    }
  };

  const handleDecision = async (decision: string) => {
    if (!selectedTicket) return;
    setActing(true);
    try {
      await recordDecision(selectedTicket.record_id, decision, operatorNotes, 'Senior Operations Lead');
      setOperatorNotes('');
      onRefreshTickets();
    } catch (e: any) {
      alert(`Decision failed: ${e.message}`);
    } finally {
      setActing(false);
    }
  };

  return (
    <section className="page">
      <div className="head-row">
        <div>
          <div className="eyebrow">Accountable Support Operations</div>
          <h1 className="title">Support ticket workspace.</h1>
          <p className="subtitle">
            Search, triage, and inspect 80 seeded synthetic tickets with transparent audit logging and human decision tracking.
          </p>
        </div>
        <button className="btn primary" onClick={onOpenCreateModal}>
          <Plus size={15} /> Create Demo Ticket
        </button>
      </div>

      <div className="panel" style={{ marginTop: '24px' }}>
        <div className="panel-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3>All Synthetic Tickets</h3>
            <span className="pill blue">{filteredTickets.length} of {tickets.length} records</span>
          </div>
        </div>

        {/* Filters */}
        <div className="filter-row">
          <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
            <input
              className="search"
              placeholder="Search by ID (e.g. MED-0003), subject, product..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label="Search tickets"
            />
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              className="select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter status"
            >
              <option value="">All Statuses</option>
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Escalated">Escalated</option>
              <option value="Resolved">Resolved</option>
              <option value="Closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Table & Detail Layout */}
        <div style={{ display: 'grid', gridTemplateColumns: selectedTicket ? '1fr 380px' : '1fr', gap: '20px' }}>
          <div style={{ overflowX: 'auto' }}>
            <table className="tickets-table">
              <thead>
                <tr>
                  <th>Ticket / Subject</th>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Escalation Risk</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.map((t) => (
                  <tr
                    key={t.record_id}
                    onClick={() => onSelectTicket(t)}
                    style={{
                      cursor: 'pointer',
                      background: selectedTicket?.record_id === t.record_id ? '#f2f8f5' : undefined,
                    }}
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
                    <td>
                      <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                        {t.escalation_score.toFixed(4)}
                      </span>
                    </td>
                  </tr>
                ))}
                {filteredTickets.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '30px', color: '#889f95' }}>
                      No matching synthetic tickets found for filter criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Ticket Detail Drawer */}
          {selectedTicket && (
            <div
              style={{
                background: '#fafcfb',
                border: '1px solid var(--line)',
                borderRadius: '14px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="ticket-id" style={{ fontSize: '15px' }}>
                  {selectedTicket.record_id}
                </span>
                <span className={getBadgeClass(selectedTicket.status)}>{selectedTicket.status}</span>
              </div>

              <div>
                <strong style={{ fontSize: '14px', color: '#274b43' }}>{selectedTicket.subject}</strong>
                <div style={{ fontSize: '11px', color: '#749288', marginTop: '4px' }}>
                  Product: <strong>{selectedTicket.product}</strong> · Category: {selectedTicket.category}
                </div>
              </div>

              <div style={{ padding: '12px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e7eeea' }}>
                <div style={{ fontSize: '11px', color: '#5f7f75' }}>
                  Days Since Created: <strong>{selectedTicket.days_since_created} days</strong>
                </div>
                <div style={{ fontSize: '11px', color: '#5f7f75', marginTop: '4px' }}>
                  Resolution Hours Target: <strong>{selectedTicket.resolution_time_hours} hrs</strong>
                </div>
                <div style={{ fontSize: '11px', color: '#5f7f75', marginTop: '4px' }}>
                  Reopen Count: <strong>{selectedTicket.reopen_count}</strong>
                </div>
                <div style={{ fontSize: '11px', color: '#5f7f75', marginTop: '4px' }}>
                  Escalation Score: <strong>{selectedTicket.escalation_score.toFixed(4)}</strong> (Threshold: 0.3667)
                </div>
              </div>

              {/* Human Decision Review Actions */}
              <div>
                <div className="eyebrow" style={{ marginBottom: '6px' }}>
                  Human Review & Resolution
                </div>
                <input
                  className="search"
                  placeholder="Reviewer notes (optional)..."
                  value={operatorNotes}
                  onChange={(e) => setOperatorNotes(e.target.value)}
                  disabled={acting}
                  style={{ marginBottom: '8px' }}
                />
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <button
                    className="btn primary"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '11px' }}
                    onClick={() => handleDecision('Approved resolution after inspection')}
                    disabled={acting || selectedTicket.status === 'Resolved'}
                  >
                    Resolve
                  </button>
                  <button
                    className="btn soft"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '11px', color: '#b3564c', background: '#fceeed' }}
                    onClick={() => handleDecision('Escalate to Senior Specialist Lead')}
                    disabled={acting || selectedTicket.status === 'Escalated'}
                  >
                    Escalate
                  </button>
                  <button
                    className="btn outline"
                    style={{ flex: 1, padding: '8px 10px', fontSize: '11px' }}
                    onClick={() => handleDecision('Case closed by operator')}
                    disabled={acting || selectedTicket.status === 'Closed'}
                  >
                    Close
                  </button>
                </div>
              </div>

              {/* Audit Timeline */}
              <div style={{ marginTop: '8px' }}>
                <div className="eyebrow" style={{ marginBottom: '6px' }}>
                  Immutable Audit Log
                </div>
                <ul className="timeline">
                  {auditEvents.map((evt) => (
                    <li key={evt.id}>
                      <strong>{evt.action} · {evt.actor}</strong>
                      <div>{evt.details}</div>
                      <div style={{ fontSize: '10px', color: '#8aa198', marginTop: '2px' }}>
                        {new Date(evt.timestamp).toLocaleString()}
                      </div>
                    </li>
                  ))}
                  {auditEvents.length === 0 && (
                    <li>
                      <strong>SEEDED · system_seed</strong>
                      <div>Initial record creation from seed 20261107</div>
                    </li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>

      <p className="foot">
        Persisted locally in SQLite (.runtime/medantrik_assist.db). All status edits write immutable audit records with actor timestamps.
      </p>
    </section>
  );
};
