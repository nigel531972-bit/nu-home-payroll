import { useState } from 'react';
import { RosterProvider } from './data/RosterContext';
import Header from './components/Header';
import RosterGrid from './components/RosterGrid';
import EmployeeManager from './components/EmployeeManager';

function App() {
  const [view, setView] = useState('roster');

  return (
    <RosterProvider>
      <div className="min-h-screen bg-gray-100">
        <Header currentView={view} onNavigate={setView} />
        <main className="max-w-screen-2xl mx-auto px-4 py-6">
          {view === 'roster' && <RosterGrid />}
          {view === 'employees' && <EmployeeManager />}
        </main>
      </div>
    </RosterProvider>
  );
}

export default App;
