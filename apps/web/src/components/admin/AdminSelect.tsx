"use client";

import { ChevronDown } from "lucide-react";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

export type AdminSelectOption = {
  value: string;
  label: string;
};

type AdminSelectProps = {
  label: ReactNode;
  value: string;
  options: AdminSelectOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  id?: string;
  /** Associates the visible label with the trigger for assistive tech. */
  labelId?: string;
};

export function AdminSelect({
  label,
  value,
  options,
  onChange,
  disabled = false,
  placeholder = "Select",
  id: idProp,
  labelId: labelIdProp,
}: AdminSelectProps) {
  const generatedId = useId();
  const generatedLabelId = useId();
  const triggerId = idProp ?? generatedId;
  const labelId = labelIdProp ?? generatedLabelId;
  const listboxId = `${triggerId}-listbox`;
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const selectedLabel =
    options.find((option) => option.value === value)?.label ?? placeholder;

  const close = useCallback((restoreFocus = true) => {
    setOpen(false);
    setActiveIndex(-1);
    if (restoreFocus) {
      requestAnimationFrame(() => {
        triggerRef.current?.focus();
      });
    }
  }, []);

  const selectIndex = useCallback(
    (index: number) => {
      const option = options[index];
      if (!option) {
        return;
      }
      onChange(option.value);
      close(true);
    },
    [close, onChange, options],
  );

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

  useEffect(() => {
    if (!open) {
      return;
    }
    const selectedIndex = options.findIndex((option) => option.value === value);
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
  }, [open, options, value]);

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) {
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setActiveIndex((current) => {
        if (options.length === 0) {
          return -1;
        }
        const next =
          event.key === "ArrowDown"
            ? (current + 1) % options.length
            : (current - 1 + options.length) % options.length;
        return next;
      });
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      if (activeIndex >= 0) {
        selectIndex(activeIndex);
      }
      return;
    }
    if (event.key === "Escape") {
      if (open) {
        event.preventDefault();
        close(true);
      }
    }
  }

  function handleListboxKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) =>
        options.length === 0 ? -1 : (current + 1) % options.length,
      );
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) =>
        options.length === 0
          ? -1
          : (current - 1 + options.length) % options.length,
      );
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (activeIndex >= 0) {
        selectIndex(activeIndex);
      }
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      close(true);
    }
    if (event.key === "Tab") {
      close(false);
    }
  }

  const activeOptionId =
    activeIndex >= 0 ? `${listboxId}-option-${activeIndex}` : undefined;

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
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={() => {
          if (disabled) {
            return;
          }
          setOpen((wasOpen) => !wasOpen);
        }}
        onKeyDown={handleTriggerKeyDown}
        className="flex w-full items-center justify-between gap-2 rounded-lg border border-ink/15 bg-paper px-4 py-3 text-left text-sm outline-none ring-sage/30 focus:border-sage focus:ring-2 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className={value ? "text-ink" : "text-ink/50"}>
          {selectedLabel}
        </span>
        <ChevronDown
          size={16}
          className="shrink-0 text-ink/50"
          aria-hidden="true"
        />
      </button>
      {open ? (
        <ul
          id={listboxId}
          role="listbox"
          aria-labelledby={triggerId}
          aria-activedescendant={activeOptionId}
          tabIndex={-1}
          onKeyDown={handleListboxKeyDown}
          ref={(node) => {
            node?.focus();
          }}
          className="absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-ink/10 bg-paper py-1 shadow-lg ring-1 ring-ink/5"
        >
          {options.map((option, index) => {
            const isSelected = option.value === value;
            const isActive = index === activeIndex;
            return (
              <li
                key={option.value || "__empty__"}
                id={`${listboxId}-option-${index}`}
                role="option"
                aria-selected={isSelected}
                className={`cursor-pointer px-4 py-2 text-sm ${
                  isActive ? "bg-sage/15 text-ink" : "text-ink/90"
                } ${isSelected ? "font-medium" : ""}`}
                onMouseEnter={() => setActiveIndex(index)}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => selectIndex(index)}
              >
                {option.label}
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
