import { Check, ChevronDown } from 'lucide-react';
import { ReactNode, useState } from 'react';
import { cn } from '../lib/cn';

export type DropdownOption = {
  value: string;
  label: string;
  icon?: ReactNode;
};

export function Dropdown({
  value,
  onChange,
  options,
  className,
  menuClassName,
  triggerIcon,
  align = 'left',
  ariaLabel,
  placeholder = 'Выбрать',
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  options: DropdownOption[];
  className?: string;
  menuClassName?: string;
  triggerIcon?: ReactNode;
  align?: 'left' | 'right';
  ariaLabel?: string;
  placeholder?: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => option.value === value);

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => setOpen((previous) => !previous)}
        className={cn(
          'focus-ring flex h-10 w-full items-center justify-between gap-2 rounded-xl border border-stone-200 bg-white px-3 text-left text-sm text-stone-900 transition-colors hover:border-stone-300 disabled:cursor-not-allowed disabled:bg-stone-50 disabled:text-stone-400',
          open && 'border-brand-400',
          className,
        )}
      >
        <span className="flex min-w-0 items-center gap-2">
          {triggerIcon}
          {selected?.icon}
          <span className="truncate">{selected ? selected.label : placeholder}</span>
        </span>
        <ChevronDown className={cn('h-4 w-4 shrink-0 text-stone-400 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <>
          <button type="button" aria-hidden tabIndex={-1} className="fixed inset-0 z-30 cursor-default" onClick={() => setOpen(false)} />
          <div
            role="listbox"
            className={cn(
              'absolute top-[calc(100%+8px)] z-40 max-h-72 min-w-full overflow-auto rounded-2xl border border-stone-200 bg-white p-1.5 shadow-soft animate-scale-in',
              align === 'right' ? 'right-0' : 'left-0',
              menuClassName,
            )}
          >
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={option.value === value}
                onClick={() => {
                  onChange(option.value);
                  setOpen(false);
                }}
                className={cn(
                  'flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left text-sm font-medium transition-colors',
                  option.value === value ? 'bg-brand-50 text-brand-700' : 'text-stone-700 hover:bg-stone-50',
                )}
              >
                <span className="flex min-w-0 items-center gap-2">
                  {option.icon}
                  <span className="truncate">{option.label}</span>
                </span>
                {option.value === value && <Check className="h-4 w-4 shrink-0" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
