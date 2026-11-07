import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { OverviewView } from './components/OverviewView';
import { ConversationsView } from './components/ConversationsView';
import { TicketsView } from './components/TicketsView';
import { KnowledgeView } from './components/KnowledgeView';
import { AnalyticsView } from './components/AnalyticsView';
import { CreateTicketModal } from './components/CreateTicketModal';
import type {
  Metrics,
  TicketInfo,
  AuditEvent,
  KnowledgeData,
} from './types';
import { fetchMetrics, fetchTickets, fetchKnowledge, fetchTicketDetail } from './services/api';
import { LayoutGrid, MessageSquare, Ticket, BookOpen, BarChart3 } from 'lucide-react';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('overview');
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<TicketInfo | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeData | null>(null);
  const [initialChatQuery, setInitialChatQuery] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [m, t, k] = await Promise.all([
        fetchMetrics(),
        fetchTickets({ limit: 100 }),
        fetchKnowledge(),
      ]);
      setMetrics(m);
      setTickets(t);
      setKnowledge(k);
      if (t.length > 0 && !selectedTicket) {
        setSelectedTicket(t[0]);
      }
    } catch (err) {
      console.error('Failed to load initial workspace data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedTicket) {
      fetchTicketDetail(selectedTicket.record_id)
        .then((data) => setAuditEvents(data.audit_events))
        .catch((err) => console.error('Failed to load audit events:', err));
    }
  }, [selectedTicket?.record_id]);

  const handleAskFromCard = (query: string) => {
    setInitialChatQuery(query);
    setActivePage('conversations');
  };

  const getPageTitle = () => {
    switch (activePage) {
      case 'overview': return lang === 'hi' ? 'अवलोकन (Overview)' : 'Overview';
      case 'conversations': return lang === 'hi' ? 'बातचीत (Conversations)' : 'Conversations';
      case 'tickets': return lang === 'hi' ? 'टिकट प्रबंधन (Support Tickets)' : 'Support Tickets';
      case 'knowledge': return lang === 'hi' ? 'ज्ञान केंद्र (Knowledge Center)' : 'Knowledge Center';
      case 'analytics': return lang === 'hi' ? 'विश्लेषण और शासन (Analytics & QA)' : 'Analytics & QA';
      default: return 'Overview';
    }
  };

  return (
    <div className="shell">
      {/* Desktop Sidebar */}
      <Sidebar
        activePage={activePage}
        onSelectPage={setActivePage}
        ticketCount={tickets.length}
      />

      {/* Main Workspace */}
      <main className="main">
        <TopBar
          pageTitle={getPageTitle()}
          lang={lang}
          onToggleLang={() => setLang((prev) => (prev === 'en' ? 'hi' : 'en'))}
        />

        {activePage === 'overview' && (
          <OverviewView
            metrics={metrics}
            recentTickets={tickets}
            onNavigate={setActivePage}
            onAskQuestion={handleAskFromCard}
            onSelectTicket={setSelectedTicket}
          />
        )}

        {activePage === 'conversations' && (
          <ConversationsView
            initialQuery={initialChatQuery}
            onClearInitialQuery={() => setInitialChatQuery('')}
            onOpenCreateTicketModal={() => setIsCreateModalOpen(true)}
            onSelectTicket={setSelectedTicket}
            onNavigateToTickets={() => setActivePage('tickets')}
          />
        )}

        {activePage === 'tickets' && (
          <TicketsView
            tickets={tickets}
            selectedTicket={selectedTicket}
            auditEvents={auditEvents}
            onSelectTicket={setSelectedTicket}
            onOpenCreateModal={() => setIsCreateModalOpen(true)}
            onRefreshTickets={loadData}
          />
        )}

        {activePage === 'knowledge' && <KnowledgeView knowledge={knowledge} />}

        {activePage === 'analytics' && <AnalyticsView metrics={metrics} />}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-nav">
        <button
          className={activePage === 'overview' ? 'active' : ''}
          onClick={() => setActivePage('overview')}
        >
          <LayoutGrid size={18} />
          <span>Home</span>
        </button>
        <button
          className={activePage === 'conversations' ? 'active' : ''}
          onClick={() => setActivePage('conversations')}
        >
          <MessageSquare size={18} />
          <span>Chat</span>
        </button>
        <button
          className={activePage === 'tickets' ? 'active' : ''}
          onClick={() => setActivePage('tickets')}
        >
          <Ticket size={18} />
          <span>Tickets</span>
        </button>
        <button
          className={activePage === 'knowledge' ? 'active' : ''}
          onClick={() => setActivePage('knowledge')}
        >
          <BookOpen size={18} />
          <span>Knowledge</span>
        </button>
        <button
          className={activePage === 'analytics' ? 'active' : ''}
          onClick={() => setActivePage('analytics')}
        >
          <BarChart3 size={18} />
          <span>Insights</span>
        </button>
      </nav>

      {/* Create Ticket Modal */}
      <CreateTicketModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onTicketCreated={loadData}
      />
    </div>
  );
};

export default App;
