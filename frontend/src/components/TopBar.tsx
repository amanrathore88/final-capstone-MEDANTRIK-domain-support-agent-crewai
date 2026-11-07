import React from 'react';
import { Languages } from 'lucide-react';

interface TopBarProps {
  pageTitle: string;
  lang: 'en' | 'hi';
  onToggleLang: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ pageTitle, lang, onToggleLang }) => {
  return (
    <header className="top">
      <div className="crumb">
        Workspace <span style={{ margin: '0 8px', color: '#c4d0cb' }}>/</span>{' '}
        <strong>{pageTitle}</strong>
      </div>

      <div className="top-right">
        <button
          className="btn outline"
          style={{ padding: '6px 12px', fontSize: '11px', display: 'flex', gap: '6px' }}
          onClick={onToggleLang}
          title="Toggle English / Hindi interface labels"
        >
          <Languages size={14} />
          <span>{lang === 'en' ? 'English (EN)' : 'हिन्दी (HI)'}</span>
        </button>

        <span className="status-badge">Simulation Active</span>
        <span className="hide-mobile" style={{ color: '#79928a', fontSize: '11px' }}>
          Student Capstone
        </span>

        <div className="avatar" style={{ height: 34, width: 34, borderRadius: 10, background: '#d9e7e2', color: '#2e6861', display: 'grid', placeItems: 'center', fontWeight: 700 }}>
          M
        </div>
      </div>
    </header>
  );
};
