import { ReactNode, useState } from 'react';
import { cn } from '../lib/cn';

export type MenuItem = {
  label: string;
  icon?: ReactNode;
  onClick: () => void;
  tone?: 'default' | 'danger';
};

export function Menu({
  children,
  items,
  triggerClassName,
  align = 'right',
  ariaLabel,
}: {
  children: ReactNode;
  items: MenuItem[];
  triggerClassName?: string;
  align?: 'left' | 'right';
  ariaLabel?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={ariaLabel}
        className={triggerClassName}
        onClick={() => setOpen((value) => !value)}
      >
        {children}
      </button>

      {open && (
        <>
          <button type="button" aria-hidden tabIndex={-1} className="fixed inset-0 z-30 cursor-default" onClick={() => setOpen(false)} />
          <div
            role="menu"
            className={cn(
              'absolute top-[calc(100%+8px)] z-40 min-w-56 animate-scale-in rounded-2xl border border-stone-200 bg-white p-1.5 shadow-soft',
              align === 'right' ? 'right-0' : 'left-0',
            )}
          >
            {items.map((item) => (
              <button
                key={item.label}
                type="button"
                role="menuitem"
                onClick={() => {
                  item.onClick();
                  setOpen(false);
                }}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm font-medium transition-colors',
                  item.tone === 'danger' ? 'text-red-600 hover:bg-red-50' : 'text-stone-700 hover:bg-stone-50',
                )}
              >
                {item.icon && <span className={cn('shrink-0', item.tone === 'danger' ? 'text-red-500' : 'text-stone-400')}>{item.icon}</span>}
                {item.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
