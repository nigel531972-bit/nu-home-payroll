import { useState } from 'react';
import { useRoster } from '../data/RosterContext';

export default function EmployeeManager() {
  const { data, getEmployeesForContract, addEmployee, removeEmployee, updateEmployee } =
    useRoster();
  const [newName, setNewName] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const contract = data.contracts[0]; // Currently just American Airlines
  const employees = getEmployeesForContract(contract.id);

  const handleAdd = (e) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    addEmployee(name, contract.id);
    setNewName('');
  };

  const handleStartEdit = (emp) => {
    setEditingId(emp.id);
    setEditName(emp.name);
  };

  const handleSaveEdit = (id) => {
    const name = editName.trim();
    if (name) {
      updateEmployee(id, { name });
    }
    setEditingId(null);
    setEditName('');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900">
            {contract.name} — Staff
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {employees.length} employee{employees.length !== 1 ? 's' : ''}{' '}
            assigned
          </p>
        </div>

        <div className="divide-y divide-gray-100">
          {employees.map((emp, idx) => (
            <div
              key={emp.id}
              className="px-6 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              {editingId === emp.id ? (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSaveEdit(emp.id);
                  }}
                  className="flex items-center gap-2 flex-1"
                >
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                  <button
                    type="submit"
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingId(null)}
                    className="text-sm text-gray-400 hover:text-gray-600"
                  >
                    Cancel
                  </button>
                </form>
              ) : (
                <>
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <span className="text-sm font-medium" style={{ color: '#1d4ed8' }}>
                      {emp.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleStartEdit(emp)}
                      className="text-sm text-gray-400 hover:text-blue-600 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => {
                        if (
                          window.confirm(
                            `Remove ${emp.name} from this contract?`
                          )
                        ) {
                          removeEmployee(emp.id);
                        }
                      }}
                      className="text-sm text-gray-400 hover:text-red-600 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}

          {employees.length === 0 && (
            <div className="px-6 py-8 text-center text-gray-400 text-sm">
              No employees assigned yet. Add one below.
            </div>
          )}
        </div>

        <form
          onSubmit={handleAdd}
          className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex gap-3"
        >
          <input
            type="text"
            placeholder="Employee full name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!newName.trim()}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Add Employee
          </button>
        </form>
      </div>
    </div>
  );
}
