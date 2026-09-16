"use client";

import { Calendar, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import {
  addCalendarMonths,
  buildCalendarGrid,
  calendarMonthLabel,
  formatAdminDateLabel,
  isDateWithinBounds,
  monthForAdminDateValue,
  todayAdminDateValue,
  type CalendarMonth,
} from "@/lib/admin-date-utils";

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

type AdminDatePickerProps = {
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  min?: string;
  max?: string;
  id?: string;
  labelId?: string;
};

export function AdminDatePicker({
  label,
  value,
  onChange,
  disabled = false,
  placeholder = "Select date",
  min,
  max,
  id: idProp,
  labelId: labelIdProp,
}: AdminDatePickerProps) {
  const generatedId = useId();
  const generatedLabelId = useId();
  const triggerId = idProp ?? generatedId;
  const labelId = labelIdProp ?? generatedLabelId;
  const dialogId = `${triggerId}-dialog`;
  const [open, setOpen] = useState(false);
  const [viewMonth, setViewMonth] = useState<CalendarMonth>(() => {
    return monthForAdminDateValue(value) ?? monthForAdminDateValue(todayAdminDateValue())!;
  });
  const [focusedValue, setFocusedValue] = useState(value || todayAdminDateValue());
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const grid = useMemo(() => buildCalendarGrid(viewMonth), [viewMonth]);

  const close = useCallback((restoreFocus = true) => {
    setOpen(false);
    if (restoreFocus) {
      requestAnimationFrame(() => {
        triggerRef.current?.focus();
      });
    }
  }, []);

  useEffect(() => {
    if (!open) {
      return;
    }
    const nextMonth =
      monthForAdminDateValue(value) ?? monthForAdminDateValue(todayAdminDateValue());
    if (nextMonth) {
      setViewMonth(nextMonth);
    }
    setFocusedValue(value || todayAdminDateValue());
  }, [open, value]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const focusedMonth = monthForAdminDateValue(focusedValue);
    if (
      focusedMonth &&
      (focusedMonth.year !== viewMonth.year || focusedMonth.month !== viewMonth.month)
    ) {
      setViewMonth(focusedMonth);
    }
  }, [focusedValue, open, viewMonth.month, viewMonth.year]);

  useEffect(() => {
    if (!open) {
      return;
    }
    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        close(true);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [close, open]);

  const selectDate = useCallback(
    (nextValue: string) => {
      if (!isDateWithinBounds(nextValue, min, max)) {
        return;
      }
      onChange(nextValue);
      close(true);
    },
    [close, max, min, onChange],
  );

  function moveFocusedDay(deltaDays: number) {
    const index = grid.findIndex((cell) => cell.value === focusedValue);
    const startIndex = index >= 0 ? index : grid.findIndex((cell) => cell.inCurrentMonth);
    const nextIndex = Math.min(Math.max(startIndex + deltaDays, 0), grid.length - 1);
    setFocusedValue(grid[nextIndex]?.value ?? focusedValue);
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) {
      return;
    }
    if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setOpen(true);
      return;
    }
    if (event.key === "Escape" && open) {
      event.preventDefault();
      close(true);
    }
  }

  function handleDialogKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      close(true);
      return;
    }
    if (event.key === "Tab") {
      close(false);
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      moveFocusedDay(-1);
      return;
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      moveFocusedDay(1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveFocusedDay(-7);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveFocusedDay(7);
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectDate(focusedValue);
    }
  }

  const displayLabel = value ? formatAdminDateLabel(value) : placeholder;

  return (
    <div ref={rootRef} className="relative block">
      <span id={labelId} className="mb-1 block text-sm font-medium text-ink">
        {label}
      </span>
      <button
        ref={triggerRef}
        id={triggerId}
        type="button"
        disabled={disabled}
        aria-labelledby={labelId}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={dialogId}
        onClick={() => {
          if (!disabled) {
            setOpen((wasOpen) => !wasOpen);
          }
        }}
        onKeyDown={handleTriggerKeyDown}
        className="flex w-full items-center justify-between gap-2 rounded-lg border border-ink/15 bg-paper px-4 py-3 text-left text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className="flex items-center gap-2">
          <Calendar size={16} className="shrink-0 text-ink/50" aria-hidden="true" />
          <span className={value ? "text-ink" : "text-ink/50"}>{displayLabel}</span>
        </span>
        <ChevronDown
          size={16}
          className="shrink-0 text-ink/50"
          aria-hidden="true"
        />
      </button>
      {open ? (
        <div
          id={dialogId}
          role="dialog"
          aria-modal="false"
          aria-label={`Choose date, ${calendarMonthLabel(viewMonth)}`}
          tabIndex={-1}
          onKeyDown={handleDialogKeyDown}
          ref={(node) => {
            node?.focus();
          }}
          className="absolute z-20 mt-1 w-full min-w-[16rem] rounded-lg border border-ink/10 bg-paper p-3 shadow-lg ring-1 ring-ink/5"
        >
          <div className="mb-3 flex items-center justify-between gap-2">
            <button
              type="button"
              aria-label="Previous month"
              className="rounded-md p-1 text-ink/70 hover:bg-ink/5 focus-visible:border-sage focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30"
              onClick={() => setViewMonth((current) => addCalendarMonths(current, -1))}
            >
              <ChevronLeft size={18} aria-hidden="true" />
            </button>
            <span className="text-sm font-semibold text-ink">
              {calendarMonthLabel(viewMonth)}
            </span>
            <button
              type="button"
              aria-label="Next month"
              className="rounded-md p-1 text-ink/70 hover:bg-ink/5 focus-visible:border-sage focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30"
              onClick={() => setViewMonth((current) => addCalendarMonths(current, 1))}
            >
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-ink/50">
            {WEEKDAY_LABELS.map((weekday) => (
              <span key={weekday} className="py-1">
                {weekday}
              </span>
            ))}
          </div>
          <div
            role="grid"
            aria-label={calendarMonthLabel(viewMonth)}
            className="mt-1 grid grid-cols-7 gap-1"
          >
            {grid.map((cell) => {
              const selected = cell.value === value;
              const focused = cell.value === focusedValue;
              const allowed = isDateWithinBounds(cell.value, min, max);
              return (
                <button
                  key={cell.value}
                  type="button"
                  role="gridcell"
                  tabIndex={focused ? 0 : -1}
                  disabled={!allowed}
                  aria-selected={selected}
                  aria-label={formatAdminDateLabel(cell.value)}
                  onFocus={() => setFocusedValue(cell.value)}
                  onMouseEnter={() => setFocusedValue(cell.value)}
                  onClick={() => selectDate(cell.value)}
                  className={`rounded-md py-2 text-sm ${
                    !cell.inCurrentMonth ? "text-ink/35" : "text-ink"
                  } ${
                    selected
                      ? "bg-sage font-semibold text-paper"
                      : focused
                        ? "bg-sage/15 text-ink"
                        : "hover:bg-ink/5"
                  } disabled:cursor-not-allowed disabled:opacity-40`}
                >
                  {cell.day}
                </button>
              );
            })}
          </div>
          <div className="mt-3 flex justify-between gap-2 border-t border-ink/10 pt-3">
            <button
              type="button"
              className="rounded-md px-2 py-1 text-xs font-medium text-ink/70 hover:bg-ink/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30"
              onClick={() => {
                onChange("");
                close(true);
              }}
            >
              Clear
            </button>
            <button
              type="button"
              className="rounded-md px-2 py-1 text-xs font-medium text-sage hover:bg-sage/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30"
              onClick={() => selectDate(todayAdminDateValue())}
            >
              Today
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
