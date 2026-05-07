/**
 * Main App component - handles routing and app state
 */

import React, { useState } from 'react';
import { Dashboard } from './pages/Dashboard';
import { ClientsPage } from './pages/ClientsPage';
import { ViolationsPage } from './pages/ViolationsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

type PageType = 'dashboard' | 'clients' | 'violations' | 'analytics';

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');

  const navigateTo = (page: string) => {
    setCurrentPage(page as PageType);
    window.scrollTo(0, 0);
  };

  const handleBack = () => {
    setCurrentPage('dashboard');
    window.scrollTo(0, 0);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentPage === 'dashboard' && <Dashboard onNavigate={navigateTo} />}
      {currentPage === 'clients' && <ClientsPage onBack={handleBack} />}
      {currentPage === 'violations' && <ViolationsPage onBack={handleBack} />}
      {currentPage === 'analytics' && <AnalyticsPage onBack={handleBack} />}
    </div>
  );
}

export default App;
