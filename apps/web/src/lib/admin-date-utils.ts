/** Calendar helpers for admin date pickers (URL values are YYYY-MM-DD, UTC-neutral). */

export const ADMIN_DATE_VALUE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

export type CalendarMonth = {
  year: number;
  month: number;
};

export function isAdminDateValue(value: string): boolean {
  return ADMIN_DATE_VALUE_PATTERN.test(value);
}

export function parseAdminDateValue(value: string): Date | null {
  if (!isAdminDateValue(value)) {
    return null;
  }
  const [year, month, day] = value.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

export function formatAdminDateValue(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatAdminDateLabel(value: string): string {
  const parsed = parseAdminDateValue(value);
  if (!parsed) {
    return value;
  }
  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

export function compareAdminDateValues(a: string, b: string): number {
  if (a === b) {
    return 0;
  }
  return a < b ? -1 : 1;
}

export function isDateWithinBounds(
  value: string,
  min?: string,
  max?: string,
): boolean {
  if (!isAdminDateValue(value)) {
    return false;
  }
  if (min && isAdminDateValue(min) && compareAdminDateValues(value, min) < 0) {
    return false;
  }
  if (max && isAdminDateValue(max) && compareAdminDateValues(value, max) > 0) {
    return false;
  }
  return true;
}

export function calendarMonthLabel({ year, month }: CalendarMonth): string {
  return new Date(Date.UTC(year, month, 1)).toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function addCalendarMonths(
  { year, month }: CalendarMonth,
  delta: number,
): CalendarMonth {
  const date = new Date(Date.UTC(year, month + delta, 1));
  return {
    year: date.getUTCFullYear(),
    month: date.getUTCMonth(),
  };
}

export type CalendarDayCell = {
  value: string;
  day: number;
  inCurrentMonth: boolean;
};

/** Sunday-start week; includes leading/trailing days for a 6-row grid when needed. */
export function buildCalendarGrid({ year, month }: CalendarMonth): CalendarDayCell[] {
  const firstOfMonth = new Date(Date.UTC(year, month, 1));
  const startOffset = firstOfMonth.getUTCDay();
  const gridStart = new Date(Date.UTC(year, month, 1 - startOffset));

  const cells: CalendarDayCell[] = [];
  for (let index = 0; index < 42; index += 1) {
    const date = new Date(
      Date.UTC(
        gridStart.getUTCFullYear(),
        gridStart.getUTCMonth(),
        gridStart.getUTCDate() + index,
      ),
    );
    cells.push({
      value: formatAdminDateValue(date),
      day: date.getUTCDate(),
      inCurrentMonth: date.getUTCMonth() === month,
    });
  }

  while (cells.length > 35 && cells.slice(35).every((cell) => !cell.inCurrentMonth)) {
    cells.pop();
  }
  return cells;
}

export function monthForAdminDateValue(value: string): CalendarMonth | null {
  const parsed = parseAdminDateValue(value);
  if (!parsed) {
    return null;
  }
  return {
    year: parsed.getUTCFullYear(),
    month: parsed.getUTCMonth(),
  };
}

export function todayAdminDateValue(): string {
  const now = new Date();
  return formatAdminDateValue(
    new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())),
  );
}
