import React, { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { createTicket } from '../services/api';

interface CreateTicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTicketCreated: () => void;
}

export const CreateTicketModal: React.FC<CreateTicketModalProps> = ({ isOpen, onClose, onTicketCreated }) => {
  const [category, setCategory] = useState('Technical Issue');
  const [severity, setSeverity] = useState('High');
  const [customerRole, setCustomerRole] = useState('Hospital Biomedical Engineer');
  const [product, setProduct] = useState('NODex');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) {
      setError('Please provide both subject and description.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await createTicket({
        category,
        severity,
        customer_role: customerRole,
        product_name: product,
        subject,
        description,
      });
      onTicketCreated();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create ticket');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: '18px', fontWeight: 800, margin: 0 }}>
              Create Synthetic Support Ticket
            </h3>
            <span style={{ fontSize: '11px', color: '#78958c' }}>
              Logged to SQLite demo database with immutable audit trace
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ border: 0, background: 'none', color: '#7a968e', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ padding: '10px 14px', background: '#fceeed', color: '#b3564c', borderRadius: '8px', fontSize: '12px', marginBottom: '14px', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label>Target Product</label>
              <select value={product} onChange={(e) => setProduct(e.target.value)}>
                <option value="NODex">NODex (Respiratory Device)</option>
                <option value="OxySense">OxySense (Oxygen Analyser)</option>
                <option value="Iron Lung">Iron Lung (Respiration System)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="Technical Issue">Technical Issue</option>
                <option value="Product Defect">Product Defect</option>
                <option value="Billing">Billing Inquiry</option>
                <option value="Account Access">Account Access</option>
                <option value="General Inquiry">General Inquiry</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label>Initial Severity</label>
              <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                <option value="Critical">Critical (Immediate Human Escalation)</option>
                <option value="High">High (24-hour SLA Target)</option>
                <option value="Medium">Medium (Standard Triage)</option>
                <option value="Low">Low (Informational)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Reporter Role</label>
              <select value={customerRole} onChange={(e) => setCustomerRole(e.target.value)}>
                <option value="Hospital Biomedical Engineer">Hospital Biomedical Engineer</option>
                <option value="Clinic Administrator">Clinic Administrator</option>
                <option value="Staff Physician">Staff Physician</option>
                <option value="Care Provider">Care Provider</option>
                <option value="Patient Caregiver">Patient Caregiver</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Subject / Issue Summary</label>
            <input
              type="text"
              placeholder="e.g., Sensor calibration drift detected during morning run"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Detailed Description</label>
            <textarea
              rows={4}
              placeholder="Provide operational details, error codes, and inspection notes..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn outline" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Demo Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
