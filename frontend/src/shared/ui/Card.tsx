import { HTMLAttributes } from 'react';
import { cn } from '../lib/cn';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_1px_2px_rgba(17,24,39,0.04)]',
        className,
      )}
      {...props}
    />
  );
}
