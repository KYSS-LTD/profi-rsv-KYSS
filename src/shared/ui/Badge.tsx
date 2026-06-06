import type { ReactNode } from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: ReactNode;
  tone?: 'blue' | 'green' | 'yellow' | 'red' | 'slate' | 'purple';
  className?: string;
}

const toneClass = {
  blue: 'bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-200',
  green: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-200',
  yellow: 'bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-200',
  red: 'bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-200',
  slate: 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200',
  purple: 'bg-violet-50 text-violet-700 dark:bg-violet-500/15 dark:text-violet-200',
};

export function Badge({ children, tone = 'slate', className }: BadgeProps) {
  return (
    <span className={clsx('inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold', toneClass[tone], className)}>
      {children}
    </span>
  );
}
