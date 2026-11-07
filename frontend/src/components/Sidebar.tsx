import React from 'react';
import { Activity, LayoutGrid, MessageSquare, Ticket, BookOpen, BarChart3 } from 'lucide-react';

interface SidebarProps {
  activePage: string;
  onSelectPage: (page: string) => void;
  ticketCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onSelectPage, ticketCount }) => {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-symbol">
          <Activity size={24} strokeWidth={2.2} />
        </div>
        <div>
          <div className="brand-title">MEDANTRIK</div>
          <div className="brand-sub">ASSIST / SUPPORT OS</div>
        </div>
      </div>

      <div>
        <div className="group-title">Workspace</div>
        <nav className="nav">
          <button
            className={activePage === 'overview' ? 'active' : ''}
            onClick={() => onSelectPage('overview')}
          >
            <LayoutGrid size={18} />
            <span>Overview</span>
          </button>

          <button
            className={activePage === 'conversations' ? 'active' : ''}
            onClick={() => onSelectPage('conversations')}
          >
            <MessageSquare size={18} />
            <span>Conversations</span>
            <span className="count">3</span>
          </button>

          <button
            className={activePage === 'tickets' ? 'active' : ''}
            onClick={() => onSelectPage('tickets')}
          >
            <Ticket size={18} />
            <span>Support Tickets</span>
            {ticketCount !== undefined && <span className="count">{ticketCount}</span>}
          </button>

          <button
            className={activePage === 'knowledge' ? 'active' : ''}
            onClick={() => onSelectPage('knowledge')}
          >
            <BookOpen size={18} />
            <span>Knowledge Center</span>
          </button>

          <button
            className={activePage === 'analytics' ? 'active' : ''}
            onClick={() => onSelectPage('analytics')}
          >
            <BarChart3 size={18} />
            <span>Analytics & QA</span>
          </button>
        </nav>
      </div>

      <div className="side-bottom">
        <div>
          <span className="orb" />
          <strong>Demo Workspace</strong>
        </div>
        <p>
          Synthetic tickets & local evidence-grounded AI. Not an official Medantrik production system.
        </p>
      </div>
    </aside>
  );
};
