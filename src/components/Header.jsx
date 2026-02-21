export default function Header({ currentView, onNavigate }) {
  return (
    <header className="bg-blue-900 text-white shadow-lg">
      <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold tracking-tight">
            Nu Home Janitorial
          </h1>
          <span className="text-blue-300 text-sm">Roster Manager</span>
        </div>
        <nav className="flex gap-1">
          <button
            onClick={() => onNavigate('roster')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              currentView === 'roster'
                ? 'bg-blue-700 text-white'
                : 'text-blue-200 hover:bg-blue-800'
            }`}
          >
            Roster
          </button>
          <button
            onClick={() => onNavigate('employees')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              currentView === 'employees'
                ? 'bg-blue-700 text-white'
                : 'text-blue-200 hover:bg-blue-800'
            }`}
          >
            Employees
          </button>
        </nav>
      </div>
    </header>
  );
}
