import { HTMLAttributes } from 'react';
import { cn } from '../lib/cn';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'grain-surface rounded-2xl border border-stone-900/[0.06] bg-white p-5 shadow-elevated',
        className,
      )}
      {...props}
    />
  );
}
