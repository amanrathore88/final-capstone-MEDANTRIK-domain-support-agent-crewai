import React, { useState } from 'react';
import { ExternalLink } from 'lucide-react';
import type { KnowledgeData } from '../types';

interface KnowledgeViewProps {
  knowledge: KnowledgeData | null;
}

export const KnowledgeView: React.FC<KnowledgeViewProps> = ({ knowledge }) => {
  const [tab, setTab] = useState<'policies' | 'products'>('policies');
  const [search, setSearch] = useState('');
  const [expandedSlug, setExpandedSlug] = useState<string | null>(null);

  const policies = knowledge?.synthetic_policies || [];
  const products = knowledge?.verified_public.products || [];
  const company = knowledge?.verified_public.company || {};

  const filteredPolicies = policies.filter(
    (p) =>
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.slug.toLowerCase().includes(search.toLowerCase()) ||
      p.content.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <section className="page">
      <div className="head-row">
        <div>
          <div className="eyebrow">Trustworthy Evidence Architecture</div>
          <h1 className="title">Knowledge center.</h1>
          <p className="subtitle">
            A strict, observable boundary between public company facts and synthetic demonstration policies created for this student capstone.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn ${tab === 'policies' ? 'primary' : 'outline'}`}
            onClick={() => setTab('policies')}
          >
            Synthetic Policies (12)
          </button>
          <button
            className={`btn ${tab === 'products' ? 'primary' : 'outline'}`}
            onClick={() => setTab('products')}
          >
            Verified Public Facts (3)
          </button>
        </div>
      </div>

      {/* Tab 1: Synthetic Policies */}
      {tab === 'policies' && (
        <div style={{ marginTop: '24px' }}>
          <div style={{ maxWidth: '400px', marginBottom: '18px' }}>
            <input
              className="search"
              placeholder="Search policies (e.g. SLA, escalation, refunds)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search policies"
            />
          </div>

          <div className="kb-cards">
            {filteredPolicies.map((p) => {
              const isExpanded = expandedSlug === p.slug;
              return (
                <div
                  key={p.slug}
                  className="kb-card"
                  style={{
                    borderColor: isExpanded ? '#15a99d' : undefined,
                    cursor: 'pointer',
                  }}
                  onClick={() => setExpandedSlug(isExpanded ? null : p.slug)}
                >
                  <span className="eyebrow" style={{ color: '#ab7a3b' }}>
                    Synthetic Demo Policy
                  </span>
                  <strong>{p.title}</strong>
                  <div style={{ fontSize: '10px', color: '#8aa096', fontFamily: 'monospace', marginBottom: '8px' }}>
                    {p.slug}.md
                  </div>
                  <p>{p.content.split('\n\n')[1] || p.content}</p>

                  <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', color: '#27786b', fontWeight: 700 }}>
                      {isExpanded ? 'Click to collapse' : 'Click to inspect full policy →'}
                    </span>
                  </div>

                  {isExpanded && (
                    <div
                      style={{
                        marginTop: '14px',
                        padding: '12px',
                        background: '#fcf8ed',
                        border: '1px solid #f0e6cd',
                        borderRadius: '8px',
                        fontSize: '11px',
                        color: '#6e5a32',
                        lineHeight: 1.6,
                      }}
                    >
                      <div style={{ fontWeight: 700, marginBottom: '4px' }}>Full Document Content:</div>
                      <div style={{ whiteSpace: 'pre-wrap' }}>{p.content}</div>
                      <div style={{ marginTop: '8px', fontStyle: 'italic', fontSize: '10px' }}>
                        Notice: This policy is a fictional test fixture for student grading and does not represent real Medantrik terms.
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 2: Verified Public Facts */}
      {tab === 'products' && (
        <div style={{ marginTop: '24px' }}>
          <div className="kb-cards">
            {products.map((prod) => (
              <div key={prod.id} className="kb-card">
                <span className="eyebrow" style={{ color: '#16766b' }}>
                  Verified Public Fact
                </span>
                <strong>{prod.name}</strong>
                <div style={{ fontSize: '11px', color: '#4a6b63', fontWeight: 600, marginBottom: '6px' }}>
                  {prod.kind}
                </div>
                <p>{prod.description}</p>
                <a
                  href={prod.source}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    marginTop: '14px',
                    color: '#158376',
                    fontSize: '11px',
                    fontWeight: 700,
                    textDecoration: 'none',
                  }}
                >
                  Verified Source: medantrik.com <ExternalLink size={11} />
                </a>
              </div>
            ))}
          </div>

          {/* Company Facts Card */}
          <div className="panel" style={{ marginTop: '24px' }}>
            <div className="panel-head">
              <h3>Company Fact Provenance</h3>
              <span className="pill green">Public Data Verified</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', fontSize: '12px', color: '#4c655e', lineHeight: 1.7 }}>
              <div>
                <strong>Legal Entity:</strong> {company.name || 'Medantrik Medtech Pvt. Ltd.'}<br />
                <strong>Incubation:</strong> {company.incubation || 'IIT Kanpur-incubated'}<br />
                <strong>Focus:</strong> {company.focus || 'Respiratory medical devices'}
              </div>
              <div>
                <strong>Office Address:</strong> {company.office || 'D-25, Sector 63A, Noida, Uttar Pradesh 201309'}<br />
                <strong>Contact Email:</strong> {company.email || 'info@medantrik.com'}<br />
                <strong>Official Site:</strong> <a href="https://medantrik.com/" target="_blank" rel="noreferrer" style={{ color: '#16766b' }}>https://medantrik.com/</a>
              </div>
              <div>
                <strong style={{ color: '#b3564c' }}>Hours Status Note:</strong><br />
                Medantrik's public contact page states Mon–Sat 9:00 AM–5:00 PM IST while footer states 9:00 AM–6:00 PM IST. The system explicitly flags this conflict and does not guarantee staffed coverage.
              </div>
            </div>
          </div>
        </div>
      )}

      <p className="foot">
        All 12 synthetic demo policies are indexed into persistent ChromaDB collections (medantrik_fixed_overlap and medantrik_sentence_based) with source metadata.
      </p>
    </section>
  );
};
