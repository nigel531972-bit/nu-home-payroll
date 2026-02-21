import {
  addDays,
  isSaturday,
  isSunday,
  getDay,
  startOfDay,
  differenceInDays,
} from 'date-fns';

/**
 * Generate roster dates from the 21st of one month to the 20th of the next.
 * @param {number} year - e.g., 2026
 * @param {number} month - 0-indexed month for the START date (e.g., 1 = February, so roster starts Feb 21)
 * @returns {Date[]} array of dates
 */
export function getRosterDates(year, month) {
  const start = new Date(year, month, 21);
  const endMonth = month + 1 > 11 ? 0 : month + 1;
  const endYear = month + 1 > 11 ? year + 1 : year;
  const end = new Date(endYear, endMonth, 20);

  const dates = [];
  let current = startOfDay(start);
  const endDate = startOfDay(end);

  while (current <= endDate) {
    dates.push(new Date(current));
    current = addDays(current, 1);
  }

  return dates;
}

/**
 * Get all weeks (Mon-Sun) that overlap with the roster period.
 * Returns arrays of indices into the dates array for each ISO week.
 */
function getWeeks(dates) {
  const weeks = [];
  let currentWeek = [];
  let lastMonday = null;

  dates.forEach((date, idx) => {
    const day = getDay(date); // 0=Sun, 1=Mon, ...
    if (day === 1 && currentWeek.length > 0) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
    currentWeek.push(idx);
  });

  if (currentWeek.length > 0) {
    weeks.push(currentWeek);
  }

  return weeks;
}

/**
 * Find all Saturday-Sunday pairs in the roster dates.
 * Returns array of [satIdx, sunIdx] pairs.
 */
function getWeekendPairs(dates) {
  const pairs = [];
  for (let i = 0; i < dates.length - 1; i++) {
    if (isSaturday(dates[i]) && isSunday(dates[i + 1])) {
      pairs.push([i, i + 1]);
    }
  }
  return pairs;
}

/**
 * Auto-generate a roster schedule.
 *
 * Rules:
 * 1. Each employee gets exactly 2 days off per week.
 * 2. Each employee must get at least one Saturday+Sunday off together per roster period.
 * 3. Weekend off assignments rotate fairly among employees.
 *
 * @param {Date[]} dates - roster dates
 * @param {Object[]} employees - array of { id, name }
 * @param {Object[]} shiftTypes - array of { id, label }
 * @returns {Object} schedule - { [employeeId]: { [dateIndex]: 'off' | shiftId } }
 */
export function autoGenerateRoster(dates, employees, shiftTypes) {
  const numEmployees = employees.length;
  const weeks = getWeeks(dates);
  const weekendPairs = getWeekendPairs(dates);
  const defaultShift = shiftTypes[0]?.id || '7/3';
  const alternateShift = shiftTypes[1]?.id || '3/7';

  // Initialize schedule: everyone works the default shift
  const schedule = {};
  employees.forEach((emp) => {
    schedule[emp.id] = {};
    dates.forEach((_, idx) => {
      schedule[emp.id][idx] = defaultShift;
    });
  });

  // Assign weekend off pairs - rotate fairly
  // With N employees and W weekends, each weekend gets floor(N/W) or ceil(N/W) people off
  // This ensures fair distribution and everyone gets at least one weekend off
  const weekendAssignments = new Array(numEmployees).fill(0);
  const numWeekends = weekendPairs.length;

  // Calculate how many employees per weekend (e.g., 8 employees / 4 weekends = 2 per weekend)
  const basePerWeekend = Math.floor(numEmployees / numWeekends);
  const extraWeekends = numEmployees % numWeekends;

  weekendPairs.forEach((pair, pairIdx) => {
    const slotsThisWeekend =
      pairIdx < extraWeekends ? basePerWeekend + 1 : basePerWeekend;

    // Pick employees who have had the fewest weekends off
    const sortedByAssignments = employees
      .map((emp, empIdx) => ({ emp, empIdx, count: weekendAssignments[empIdx] }))
      .sort((a, b) => a.count - b.count);

    const selected = sortedByAssignments.slice(0, slotsThisWeekend);

    selected.forEach(({ emp, empIdx }) => {
      schedule[emp.id][pair[0]] = 'off'; // Saturday
      schedule[emp.id][pair[1]] = 'off'; // Sunday
      weekendAssignments[empIdx]++;
    });
  });

  // Now ensure each employee has the right number of days off per week.
  // For partial weeks (less than 5 days), scale proportionally:
  //   7 days -> 2 off, 5-6 days -> 2 off, 3-4 days -> 1 off, 1-2 days -> 0 off
  weeks.forEach((weekIndices) => {
    const weekLen = weekIndices.length;
    const targetOff = weekLen >= 5 ? 2 : weekLen >= 3 ? 1 : 0;

    employees.forEach((emp) => {
      let daysOff = weekIndices.filter(
        (idx) => schedule[emp.id][idx] === 'off'
      ).length;

      if (daysOff < targetOff) {
        // Need to add more days off - prefer weekdays
        const workingDays = weekIndices.filter(
          (idx) => schedule[emp.id][idx] !== 'off'
        );

        // Prefer midweek days (Tue, Wed, Thu) for extra days off
        const preferred = workingDays
          .map((idx) => ({ idx, day: getDay(dates[idx]) }))
          .sort((a, b) => {
            const pref = { 3: 0, 4: 1, 2: 2, 1: 3, 5: 4, 6: 5, 0: 6 };
            return (pref[a.day] ?? 7) - (pref[b.day] ?? 7);
          });

        const needed = targetOff - daysOff;
        for (let i = 0; i < needed && i < preferred.length; i++) {
          schedule[emp.id][preferred[i].idx] = 'off';
        }
      } else if (daysOff > targetOff) {
        // Too many days off - convert some back to working
        const offDays = weekIndices.filter(
          (idx) => schedule[emp.id][idx] === 'off'
        );
        const nonWeekendOff = offDays.filter(
          (idx) => !isSaturday(dates[idx]) && !isSunday(dates[idx])
        );
        // For assigned weekend-off weeks, keep the weekend pair and remove weekday offs
        const weekendOff = offDays.filter(
          (idx) => isSaturday(dates[idx]) || isSunday(dates[idx])
        );

        let excess = daysOff - targetOff;
        // Remove non-weekend off days first
        for (let i = 0; i < excess && i < nonWeekendOff.length; i++) {
          schedule[emp.id][nonWeekendOff[i]] = defaultShift;
        }
      }
    });
  });

  // Assign alternating shifts to create coverage balance
  // Split employees roughly in half between the two shifts
  const halfPoint = Math.ceil(numEmployees / 2);
  employees.forEach((emp, empIdx) => {
    const shift = empIdx < halfPoint ? defaultShift : alternateShift;
    dates.forEach((_, idx) => {
      if (schedule[emp.id][idx] !== 'off') {
        schedule[emp.id][idx] = shift;
      }
    });
  });

  return schedule;
}

/**
 * Validate a roster schedule against the rules.
 * Returns an array of violation objects.
 */
export function validateRoster(dates, employees, schedule) {
  const violations = [];
  const weeks = getWeeks(dates);
  const weekendPairs = getWeekendPairs(dates);

  employees.forEach((emp) => {
    const empSchedule = schedule[emp.id];
    if (!empSchedule) return;

    // Check: correct days off per week (2 for full weeks, scaled for partial)
    weeks.forEach((weekIndices, weekNum) => {
      const weekLen = weekIndices.length;
      const targetOff = weekLen >= 5 ? 2 : weekLen >= 3 ? 1 : 0;
      const daysOff = weekIndices.filter(
        (idx) => empSchedule[idx] === 'off'
      ).length;
      if (daysOff < targetOff) {
        violations.push({
          type: 'insufficient_days_off',
          employeeId: emp.id,
          employeeName: emp.name,
          week: weekNum + 1,
          daysOff,
          message: `${emp.name} has only ${daysOff} day(s) off in week ${weekNum + 1} (needs ${targetOff})`,
        });
      }
    });

    // Check: at least one Saturday+Sunday pair off
    const hasWeekendOff = weekendPairs.some(
      ([satIdx, sunIdx]) =>
        empSchedule[satIdx] === 'off' && empSchedule[sunIdx] === 'off'
    );
    if (!hasWeekendOff) {
      violations.push({
        type: 'no_weekend_off',
        employeeId: emp.id,
        employeeName: emp.name,
        message: `${emp.name} has no Saturday+Sunday off together in this roster period`,
      });
    }
  });

  return violations;
}
