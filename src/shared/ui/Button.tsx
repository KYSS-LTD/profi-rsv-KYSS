import type { ButtonHTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md';
  children: ReactNode;
}

export function Button({ variant = 'primary', size = 'md', className, children, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-2xl font-semibold transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50',
        size === 'sm' ? 'px-3 py-2 text-xs' : 'px-4 py-3 text-sm',
        variant === 'primary' && 'bg-tg-button text-tg-buttonText shadow-soft hover:brightness-95',
        variant === 'secondary' && 'bg-slate-100 text-slate-800 hover:bg-slate-200 dark:bg-white/10 dark:text-white dark:hover:bg-white/15',
        variant === 'ghost' && 'text-tg-text hover:bg-black/5 dark:hover:bg-white/10',
        variant === 'danger' && 'bg-rose-50 text-rose-700 hover:bg-rose-100 dark:bg-rose-500/15 dark:text-rose-200',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
