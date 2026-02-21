const STORAGE_KEY = 'nu-home-roster-data';

const DEFAULT_DATA = {
  contracts: [
    {
      id: 'american-airlines',
      name: 'American Airlines',
      shiftTypes: [
        { id: '7/3', label: '7/3', startTime: '19:00', endTime: '03:00' },
        { id: '3/7', label: '3/7', startTime: '03:00', endTime: '19:00' },
      ],
      rosterStartDay: 21,
    },
  ],
  employees: [
    { id: '1', name: 'Alicia Brown', contractId: 'american-airlines' },
    { id: '2', name: 'Taylor Simpson', contractId: 'american-airlines' },
    { id: '3', name: 'Annmarie Cox', contractId: 'american-airlines' },
    { id: '4', name: 'Sherlyn Grant', contractId: 'american-airlines' },
    { id: '5', name: 'Leisa Young', contractId: 'american-airlines' },
    { id: '6', name: 'Lima St. John', contractId: 'american-airlines' },
    { id: '7', name: 'Venista Hackett', contractId: 'american-airlines' },
    { id: '8', name: 'Marcia James', contractId: 'american-airlines' },
  ],
  rosters: {},
};

export function loadData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch {
    // ignore corrupted data
  }
  return structuredClone(DEFAULT_DATA);
}

export function saveData(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}
