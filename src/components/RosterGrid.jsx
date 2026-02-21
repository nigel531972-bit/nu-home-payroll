import { useState, useMemo } from 'react';
import { format, isSaturday, isSunday, getDay } from 'date-fns';
import { useRoster } from '../data/RosterContext';
import {
  getRosterDates,
  autoGenerateRoster,
  validateRoster,
} from '../data/scheduler';

const DAY_ABBREVS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function CellEditor({ value, shiftTypes, onSave, onCancel }) {
  const options = ['off', ...shiftTypes.map((s) => s.id)];
  return (
    <select
      autoFocus
      value={value}
      onChange={(e) => onSave(e.target.value)}
      onBlur={onCancel}
      className="w-full h-full text-xs text-center bg-white border-2 border-blue-500 rounded focus:outline-none"
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt === 'off' ? 'OFF' : opt}
        </option>
      ))}
    </select>
  );
}

export default function RosterGrid() {
  const { data, getEmployeesForContract, getRoster, saveRoster } = useRoster();
  const contract = data.contracts[0];
  const employees = getEmployeesForContract(contract.id);

  const now = new Date();
  const [rosterYear, setRosterYear] = useState(now.getFullYear());
  const [rosterMonth, setRosterMonth] = useState(
    now.getDate() >= 21 ? now.getMonth() : now.getMonth() - 1 < 0 ? 11 : now.getMonth() - 1
  );

  const [editingCell, setEditingCell] = useState(null); // { empId, dateIdx }
  const [showViolations, setShowViolations] = useState(false);

  const dates = useMemo(
    () => getRosterDates(rosterYear, rosterMonth),
    [rosterYear, rosterMonth]
  );

  const rosterKey = `${contract.id}-${rosterYear}-${rosterMonth}`;
  const schedule = getRoster(contract.id, rosterYear, rosterMonth);

  const violations = useMemo(() => {
    if (!schedule) return [];
    return validateRoster(dates, employees, schedule);
  }, [schedule, dates, employees]);

  const violationsByEmployee = useMemo(() => {
    const map = {};
    violations.forEach((v) => {
      if (!map[v.employeeId]) map[v.employeeId] = [];
      map[v.employeeId].push(v);
    });
    return map;
  }, [violations]);

  const handleGenerate = () => {
    const newSchedule = autoGenerateRoster(
      dates,
      employees,
      contract.shiftTypes
    );
    saveRoster(contract.id, rosterYear, rosterMonth, newSchedule);
  };

  const handleCellClick = (empId, dateIdx) => {
    if (!schedule) return;
    setEditingCell({ empId, dateIdx });
  };

  const handleCellSave = (empId, dateIdx, value) => {
    const updated = { ...schedule };
    updated[empId] = { ...updated[empId], [dateIdx]: value };
    saveRoster(contract.id, rosterYear, rosterMonth, updated);
    setEditingCell(null);
  };

  const navigateMonth = (dir) => {
    let newMonth = rosterMonth + dir;
    let newYear = rosterYear;
    if (newMonth > 11) {
      newMonth = 0;
      newYear++;
    } else if (newMonth < 0) {
      newMonth = 11;
      newYear--;
    }
    setRosterMonth(newMonth);
    setRosterYear(newYear);
  };

  const monthLabel = format(new Date(rosterYear, rosterMonth, 21), 'MMM yyyy');
  const endMonth = rosterMonth + 1 > 11 ? 0 : rosterMonth + 1;
  const endYear = rosterMonth + 1 > 11 ? rosterYear + 1 : rosterYear;
  const endLabel = format(new Date(endYear, endMonth, 20), 'MMM dd, yyyy');
  const startLabel = format(
    new Date(rosterYear, rosterMonth, 21),
    'MMM dd, yyyy'
  );

  const getCellColor = (value, date) => {
    if (value === 'off') {
      if (isSaturday(date) || isSunday(date)) {
        return 'bg-green-100 text-green-800 font-semibold';
      }
      return 'bg-yellow-50 text-yellow-700 font-semibold';
    }
    if (value === '7/3') return 'bg-blue-50 text-blue-800';
    if (value === '3/7') return 'bg-purple-50 text-purple-800';
    return 'bg-gray-50 text-gray-700';
  };

  const isWeekend = (date) => isSaturday(date) || isSunday(date);

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-4 py-3 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-900">
            {contract.name}
          </h2>
          <span className="text-sm text-gray-400">|</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigateMonth(-1)}
              className="w-8 h-8 rounded-lg border border-gray-300 flex items-center justify-center text-gray-500 hover:bg-gray-100 transition-colors"
            >
              &lt;
            </button>
            <span className="text-sm font-medium text-gray-700 min-w-[220px] text-center">
              {startLabel} — {endLabel}
            </span>
            <button
              onClick={() => navigateMonth(1)}
              className="w-8 h-8 rounded-lg border border-gray-300 flex items-center justify-center text-gray-500 hover:bg-gray-100 transition-colors"
            >
              &gt;
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {violations.length > 0 && (
            <button
              onClick={() => setShowViolations(!showViolations)}
              className="text-sm px-3 py-1.5 rounded-lg bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
            >
              {violations.length} issue{violations.length !== 1 ? 's' : ''}
            </button>
          )}
          <button
            onClick={handleGenerate}
            disabled={employees.length === 0}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {schedule ? 'Re-generate Roster' : 'Auto-generate Roster'}
          </button>
        </div>
      </div>

      {/* Violations panel */}
      {showViolations && violations.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4">
          <h3 className="text-sm font-semibold text-red-800 mb-2">
            Schedule Violations
          </h3>
          <ul className="space-y-1">
            {violations.map((v, i) => (
              <li key={i} className="text-sm text-red-700">
                {v.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-blue-50 border border-blue-200"></span>
          7/3 (7PM–3AM)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-purple-50 border border-purple-200"></span>
          3/7 (3AM–7PM)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-yellow-50 border border-yellow-200"></span>
          Off (weekday)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-4 rounded bg-green-100 border border-green-200"></span>
          Off (weekend)
        </span>
      </div>

      {/* Grid */}
      {employees.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-12 text-center text-gray-400">
          <p>No employees assigned to this contract.</p>
          <p className="text-sm mt-1">
            Add employees in the Employees tab first.
          </p>
        </div>
      ) : !schedule ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-12 text-center text-gray-400">
          <p>No roster generated yet for this period.</p>
          <p className="text-sm mt-1">
            Click "Auto-generate Roster" to create one.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="bg-gray-50">
                  <th className="sticky left-0 z-10 bg-gray-50 px-3 py-2 text-left text-xs font-semibold text-gray-600 border-b border-r border-gray-200 min-w-[140px]">
                    Employee
                  </th>
                  {dates.map((date, idx) => (
                    <th
                      key={idx}
                      className={`px-1 py-1.5 text-center border-b border-gray-200 min-w-[44px] ${
                        isWeekend(date)
                          ? 'bg-gray-100'
                          : ''
                      }`}
                    >
                      <div className="text-[10px] text-gray-400">
                        {DAY_ABBREVS[getDay(date)]}
                      </div>
                      <div
                        className={`text-xs font-medium ${
                          isWeekend(date) ? 'text-blue-700' : 'text-gray-700'
                        }`}
                      >
                        {format(date, 'd')}
                      </div>
                    </th>
                  ))}
                  <th className="px-3 py-2 text-center border-b border-l border-gray-200 text-xs font-semibold text-gray-600 min-w-[50px]">
                    Off
                  </th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp) => {
                  const empSchedule = schedule[emp.id] || {};
                  const hasViolation = !!violationsByEmployee[emp.id];
                  const totalOff = Object.values(empSchedule).filter(
                    (v) => v === 'off'
                  ).length;

                  return (
                    <tr
                      key={emp.id}
                      className={`border-b border-gray-100 hover:bg-gray-50/50 ${
                        hasViolation ? 'bg-red-50/30' : ''
                      }`}
                    >
                      <td
                        className={`sticky left-0 z-10 px-3 py-2 text-sm font-medium border-r border-gray-200 ${
                          hasViolation
                            ? 'bg-red-50 text-red-800'
                            : 'bg-white text-gray-900'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {hasViolation && (
                            <span
                              className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0"
                              title={violationsByEmployee[emp.id]
                                .map((v) => v.message)
                                .join('\n')}
                            ></span>
                          )}
                          <span className="truncate">{emp.name}</span>
                        </div>
                      </td>
                      {dates.map((date, idx) => {
                        const value = empSchedule[idx] || '—';
                        const isEditing =
                          editingCell?.empId === emp.id &&
                          editingCell?.dateIdx === idx;

                        return (
                          <td
                            key={idx}
                            onClick={() => handleCellClick(emp.id, idx)}
                            className={`px-0.5 py-1.5 text-center border-r border-gray-100 cursor-pointer transition-colors ${
                              isWeekend(date)
                                ? 'border-r-gray-200'
                                : ''
                            } ${value !== '—' ? getCellColor(value, date) : 'text-gray-300'}`}
                          >
                            {isEditing ? (
                              <CellEditor
                                value={value}
                                shiftTypes={contract.shiftTypes}
                                onSave={(v) =>
                                  handleCellSave(emp.id, idx, v)
                                }
                                onCancel={() => setEditingCell(null)}
                              />
                            ) : (
                              <span className="text-[11px]">
                                {value === 'off' ? 'OFF' : value}
                              </span>
                            )}
                          </td>
                        );
                      })}
                      <td className="px-2 py-1.5 text-center border-l border-gray-200 text-xs font-medium text-gray-600">
                        {totalOff}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
