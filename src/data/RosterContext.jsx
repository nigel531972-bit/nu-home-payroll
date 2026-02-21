import { createContext, useContext, useState, useCallback } from 'react';
import { loadData, saveData, generateId } from './store';

const RosterContext = createContext(null);

export function RosterProvider({ children }) {
  const [data, setData] = useState(loadData);

  const persist = useCallback((updater) => {
    setData((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      saveData(next);
      return next;
    });
  }, []);

  // Contract helpers
  const getContract = useCallback(
    (id) => data.contracts.find((c) => c.id === id),
    [data.contracts]
  );

  // Employee helpers
  const getEmployeesForContract = useCallback(
    (contractId) => data.employees.filter((e) => e.contractId === contractId),
    [data.employees]
  );

  const addEmployee = useCallback(
    (name, contractId) => {
      persist((prev) => ({
        ...prev,
        employees: [
          ...prev.employees,
          { id: generateId(), name, contractId },
        ],
      }));
    },
    [persist]
  );

  const removeEmployee = useCallback(
    (id) => {
      persist((prev) => ({
        ...prev,
        employees: prev.employees.filter((e) => e.id !== id),
      }));
    },
    [persist]
  );

  const updateEmployee = useCallback(
    (id, updates) => {
      persist((prev) => ({
        ...prev,
        employees: prev.employees.map((e) =>
          e.id === id ? { ...e, ...updates } : e
        ),
      }));
    },
    [persist]
  );

  // Roster helpers
  const getRosterKey = (contractId, year, month) =>
    `${contractId}-${year}-${month}`;

  const getRoster = useCallback(
    (contractId, year, month) => {
      const key = getRosterKey(contractId, year, month);
      return data.rosters[key] || null;
    },
    [data.rosters]
  );

  const saveRoster = useCallback(
    (contractId, year, month, schedule) => {
      const key = getRosterKey(contractId, year, month);
      persist((prev) => ({
        ...prev,
        rosters: {
          ...prev.rosters,
          [key]: schedule,
        },
      }));
    },
    [persist]
  );

  const value = {
    data,
    getContract,
    getEmployeesForContract,
    addEmployee,
    removeEmployee,
    updateEmployee,
    getRoster,
    saveRoster,
  };

  return (
    <RosterContext.Provider value={value}>{children}</RosterContext.Provider>
  );
}

export function useRoster() {
  const ctx = useContext(RosterContext);
  if (!ctx) throw new Error('useRoster must be used within RosterProvider');
  return ctx;
}
